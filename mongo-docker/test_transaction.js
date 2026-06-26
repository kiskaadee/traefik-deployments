// Test multi-document transaction support
print("Testing multi-document transaction support...");

// Create test collections
db = db.getSiblingDB('testdb');

// Clear any existing test data
db.users.deleteMany({});
db.accounts.deleteMany({});

print("Starting transaction test...");

const session = db.getMongo().startSession();
session.startTransaction();

try {
    const sessionDb = session.getDatabase('testdb');
    
    // Insert into first collection within transaction
    sessionDb.users.insertOne({
        _id: 1, 
        name: "Alice", 
        email: "alice@example.com"
    });
    
    // Insert into second collection within transaction
    sessionDb.accounts.insertOne({
        _id: 1, 
        userId: 1, 
        balance: 1000
    });
    
    // Update within transaction
    sessionDb.accounts.updateOne(
        {_id: 1}, 
        {$inc: {balance: -100}}
    );
    
    // Commit the transaction
    session.commitTransaction();
    print("✅ Transaction committed successfully!");
    
} catch (error) {
    print("❌ Transaction failed: " + error);
    session.abortTransaction();
} finally {
    session.endSession();
}

// Verify the data was committed
print("\nVerifying transaction results:");
print("Users count: " + db.users.countDocuments());
print("Accounts count: " + db.accounts.countDocuments());

const account = db.accounts.findOne({_id: 1});
if (account) {
    print("Final account balance: " + account.balance);
    if (account.balance === 900) {
        print("✅ Multi-document transactions are working correctly!");
    } else {
        print("❌ Transaction data inconsistent");
    }
} else {
    print("❌ No account data found");
}

print("\nTransaction test completed.");