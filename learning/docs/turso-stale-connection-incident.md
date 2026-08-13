# Turso / SQLAlchemy Stale Connection Failure

## Context

The application worked normally most of the time, but periodically the API would begin returning database-related 500 errors. Restarting the service restored normal operation, but the underlying cause was initially unclear.

The important failure was:

ValueError: Hrana: `api error: status=404 Not Found,
body={"error":"stream not found: 112ed9b2:3d0910"}`

The error occurred while executing an otherwise normal query:

db.query(models.ORMCourse).all()

The traceback showed the failure propagating through SQLAlchemy and the database driver until it became a ValueError originating from Hrana.

1. The Mental Model: What Is a Database Connection?

A database connection is not a pointer to the database or to a particular piece of data.

It is better understood as a reusable communication channel/handle through which the application and database exchange messages.

Conceptually:

Application
    │
    │ database protocol messages
    ▼
Connection
    │
    ▼
Database server

For a remote database, several layers can exist underneath the database connection abstraction:

SQLAlchemy Connection
        │
        ▼
Database driver
        │
        ▼
Hrana
        │
        ▼
WebSocket
        │
        ▼
Network
        │
        ▼
Turso

A SQL statement such as:

SELECT * FROM courses;

is a message sent through a connection. The connection is not the query itself and does not contain the database's data.

2. Why SQLAlchemy Uses a Connection Pool

Opening a connection can require establishing network and protocol state, authenticating, and performing other setup work.

Creating a new connection for every request would therefore be wasteful:

Request 1 → open connection → query → close
Request 2 → open connection → query → close
Request 3 → open connection → query → close

SQLAlchemy instead maintains a connection pool.

The pool contains multiple reusable connections to the same database:

                 Turso
                   ▲
             ┌─────┼─────┐
             │     │     │
          Conn A Conn B Conn C
             ▲     ▲     ▲
             └─────┼─────┘
                   │
             Connection Pool

A request can borrow a connection:

Request
   │
   ▼
Pool
   │
   ▼
Connection B
   │
   ▼
execute SQL

When the request finishes, the connection can be returned to the pool and reused by another request.

Important consequence

A connection in a pool may remain alive for much longer than the request that originally used it.

Therefore:

A connection can become stale while sitting inside the pool.

This is the central concept behind the incident.

3. What Went Wrong

The application was using a remote Turso database through the Hrana protocol.

The important conceptual chain was:

FastAPI
   │
   ▼
SQLAlchemy Session
   │
   ▼
SQLAlchemy Engine
   │
   ▼
Connection Pool
   │
   ▼
Database Connection
   │
   ▼
Hrana / WebSocket
   │
   ▼
Turso

A pooled connection could become invalid independently of the Python process.

For example:

Connection Pool

┌─────────────────────────────┐
│ Connection A → healthy      │
│ Connection B → healthy      │
│ Connection C → healthy      │
└─────────────────────────────┘

Later, the underlying communication associated with Connection B could disappear or become invalid:

Connection Pool

┌─────────────────────────────┐
│ Connection A → healthy      │
│ Connection B → stale/dead  │
│ Connection C → healthy      │
└─────────────────────────────┘

The pool could still contain a connection object representing B.

A later request could therefore receive B:

GET /api/courses
      │
      ▼
borrow Connection B
      │
      ▼
execute SELECT
      │
      ▼
Hrana
      │
      ▼
"stream not found"

The database itself was not necessarily unavailable. The problem was that the application attempted to use an invalid communication state.

4. Why the Error Was Intermittent

This explains why the dashboard could work normally and then suddenly fail.

Suppose the pool contains:

A → healthy
B → stale
C → healthy

Requests using A or C succeed:

Request → A → success
Request → C → success
Request → A → success

A request that receives B fails:

Request → B → "stream not found"

This produces an apparently random failure from the API's perspective.

It also explains why restarting the service appeared to fix the problem.

A restart destroys the old:

SQLAlchemy engine

connection pool

connection objects

underlying driver state

The new process creates fresh connections and therefore fresh communication state.

5. Why pool_pre_ping=True Was Added

The first change was:

pool_pre_ping=True

The purpose is to test a pooled connection before reusing it.

Without a health check:

borrow connection
      │
      ▼
assume it is valid
      │
      ▼
execute query
      │
      ▼
possible stale-connection failure

With pre-ping:

borrow connection
      │
      ▼
test connection
      │
   ┌──┴──┐
   │     │
healthy  dead
   │     │
   │     ▼
   │   discard /
   │   replace
   │
   ▼
execute query

The important idea is:

A connection retrieved from a pool is not automatically guaranteed to still be usable.

pool_pre_ping makes SQLAlchemy perform a liveness check before trusting a pooled connection.

6. Why pool_recycle=300 Was Added

The second change was:

pool_recycle=300

This puts an age limit on pooled connections.

Conceptually:

Connection created
      │
      ▼
     0 s
      │
      │
      ▼
    300 s
      │
      ▼
connection is recycled

This is different from pool_pre_ping.

pool_pre_ping

Asks:

"Is this connection still usable?"

pool_recycle

Asks:

"Has this connection been around long enough that we should replace it?"

So pool_recycle is a preventative measure against keeping connections alive indefinitely.

7. Why a Custom handle_error Listener Was Needed

The third and most specific change was:

from sqlalchemy import event
from sqlalchemy.engine import ExceptionContext

followed by:

@event.listens_for(engine, "handle_error")
def handle_exception(context: ExceptionContext) -> None:
    orig = context.original_exception

    if orig and any(
        msg in str(orig)
        for msg in (
            "stream not found",
            "WebSocket was closed",
            "closed websocket",
        )
    ):
        context.is_disconnect = True

This exists because the database driver produced a Hrana-specific error:

ValueError:
Hrana: api error: status=404
...
"stream not found"

The important part is that this error is not necessarily represented by an exception type that SQLAlchemy automatically recognizes as a disconnected database connection.

SQLAlchemy therefore needs help interpreting this particular error.

The handler effectively tells SQLAlchemy:

"When this specific Hrana/WebSocket failure occurs, consider the connection disconnected."

Setting:

context.is_disconnect = True

allows SQLAlchemy's connection-management machinery to treat the connection as invalid rather than as an ordinary query error.

Conceptually:

Hrana
   │
   ▼
"stream not found"
   │
   ▼
driver raises exception
   │
   ▼
SQLAlchemy handle_error
   │
   ▼
recognize Hrana disconnect
   │
   ▼
context.is_disconnect = True
   │
   ▼
connection is invalidated
   │
   ▼
fresh connection can be established

This is preferable to putting special reconnect logic inside individual CRUD endpoints.

8. Why These Three Changes Complement Each Other

The three changes operate at different points in the connection lifecycle.

Change

Main purpose

pool_pre_ping=True

Detect stale connections before reusing them

pool_recycle=300

Prevent connections from remaining in the pool indefinitely

handle_error + is_disconnect=True

Teach SQLAlchemy that specific Hrana/WebSocket errors mean the connection is dead

Together:

                 CONNECTION POOL
                       │
          ┌────────────┴────────────┐
          │                         │
     recycle age                pre-ping
          │                         │
          └────────────┬────────────┘
                       │
                stale connection
                       │
                       ▼
                 Hrana failure
                       │
                       ▼
                handle_error
                       │
                       ▼
             mark as disconnect
                       │
                       ▼
             invalidate connection
                       │
                       ▼
              establish fresh one

The goal is not to make connections immortal.

The goal is to make the application resilient to connection failure.

9. What Was Actually "Wrong" With the Original Application?

The CRUD code itself was not fundamentally wrong.

For example:

def get_courses(db: Session):
    return list(db.query(models.ORMCourse).all())

is a normal use of SQLAlchemy.

The problem was an implicit assumption:

"If SQLAlchemy gives me a connection from its pool, that connection is still valid."

That assumption can fail with long-lived remote connections.

The more useful backend lesson is:

A connection pool is a cache of reusable communication channels, and cached connections can become stale.

This is broader and more useful than memorizing pool_pre_ping.

10. What the Error Does and Does Not Prove

The observed error was:

stream not found

This establishes that the client attempted to use a Hrana stream that Turso no longer recognized.

It strongly supports the stale/invalid connection explanation.

However, the traceback alone does not establish the precise reason why the stream became invalid.

Possible underlying causes could include:

WebSocket interruption

network interruption

server-side stream cleanup or expiration

another connection-lifecycle event

Therefore the diagnosis should distinguish between:

Established

The application attempted to use an invalid Hrana stream.

Strong inference

A stale pooled connection was reused.

Not established from this evidence alone

The exact event that caused Turso to discard the stream.

This distinction is important when debugging infrastructure problems.

11. Debugging Lesson

The failure initially appeared to be:

/api/courses is randomly returning 500

But the useful debugging path was to follow the exception downward:

HTTP request
    ↓
FastAPI route
    ↓
controller
    ↓
SQLAlchemy Session
    ↓
SQLAlchemy Connection
    ↓
database driver
    ↓
Hrana
    ↓
"stream not found"

The lower-level error contained more information than the HTTP 500.

When debugging database failures, investigate not only:

"What SQL query failed?"

but also:

"What communication channel was being used to execute it, and what is its lifecycle?"

That distinction is particularly important for remote databases and connection pools.

12. Final Mental Model

The most useful mental model for this incident is:

Database
  │
  │ stores data
  │
  ▼
Connection
  │
  │ communication channel / handle
  │
  ▼
Connection Pool
  │
  │ caches reusable connections
  │
  ▼
SQLAlchemy
  │
  │ borrows connections for database work
  │
  ▼
Application

A connection is not the data.

A connection is not the query.

A connection is not merely a pointer to a database.

It is a reusable means of communicating with the database, represented to the application by a connection object and backed by lower-level protocol/network state.

The incident happened because that communication state could become invalid while the corresponding connection remained available to SQLAlchemy's pool.

The fix therefore belongs at the connection-management layer rather than in the CRUD logic.



