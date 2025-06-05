// MongoDB Setup Commands

// Tạo database
use emotional_diary_db

// Tạo collections
db.createCollection("users")
db.createCollection("entries")
db.createCollection("emotions")

// Tạo indexes cho tối ưu hiệu năng
db.entries.createIndex({ "content": "text" })  // Full-text search index
db.entries.createIndex({ "user_id": 1 })       // Query by user
db.entries.createIndex({ "date": -1 })         // Sort by date
db.emotions.createIndex({ "user_id": 1 })      // Query by user
db.emotions.createIndex({ "entry_id": 1 })     // Query by entry
db.emotions.createIndex({ 
    "user_id": 1, 
    "entry_id": 1 
}, { unique: true })                           // Unique compound index

// Validator cho collection users
db.runCommand({
    collMod: "users",
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["username", "password"],
            properties: {
                username: {
                    bsonType: "string",
                    minLength: 3,
                    maxLength: 50
                },
                password: {
                    bsonType: "string",
                    minLength: 60,
                    maxLength: 60
                }
            }
        }
    }
})

// Validator cho collection entries
db.runCommand({
    collMod: "entries",
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["date", "content", "user_id"],
            properties: {
                date: {
                    bsonType: "string",
                    pattern: "^\\d{4}-\\d{2}-\\d{2}$"
                },
                content: {
                    bsonType: "string",
                    minLength: 1
                },
                emotions: {
                    bsonType: "array",
                    items: {
                        bsonType: "string"
                    }
                },
                user_id: {
                    bsonType: "objectId"
                }
            }
        }
    }
})

// Validator cho collection emotions
db.runCommand({
    collMod: "emotions",
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["user_id", "entry_id", "sentiment"],
            properties: {
                user_id: {
                    bsonType: "objectId"
                },
                entry_id: {
                    bsonType: "objectId"
                },
                sentiment: {
                    enum: ["positive", "neutral", "negative"]
                },
                icon: {
                    bsonType: "string"
                }
            }
        }
    }
})
