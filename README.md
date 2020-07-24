# COSMOSQL - Alpha

A portable and universal query language. Write your queries once. Run everywhere.

## Uses cases
* When you want to query unconventional data like flat files.
* When you change between SQL and NoSQL.
* When you just want to "dump" some data.
* When you get tired of using an ORM.
* When you want to work more on the data than the database.

## What is the repository for?
The repository exists because the grammar for the query language is written in Python using the PyParsing package. The parsed results are a bit cryptic so there is a class that organizes the results and makes parsing easy.

## Examples
Some of the translated queries may not be accurate. Especially ones that parse through flat files.

For the sake of keeping the README compact, all queries are written in one line. **White space does not matter.**
#### Select all users
```
SELECT users
```
* **MySQL**: `SELECT * FROM users`
* **Mongo**: `db.users.find()`
* **JSON**: `tables['users']['entries']`
* **CSV**: `[line.split() for line in open('users.csv')][1:]`

#### Select the name and email from all users
```
SELECT users(name,email)
```
* **MySQL**: `SELECT name, email FROM users`
* **Mongo**: `db.users.find({}, {_id:0, name:1, email:1})`
* **JSON**: `list(map(lambda entry: {key: entry[key] for key in ('name', 'email')}, entries))`
* **CSV**: See json

#### Select name and email from all users whose age is greater than 21
```
SELECT users(name,email){ WHERE(age > 21) }
```
* **MySQL**: `SELECT name, email FROM users WHERE age > 21`
* **Mongo**: `db.users.find({age:{$gt:21}}, {_id:0, name:1, email:1})`
* **JSON**: `list(map(lambda entry: {key: entry[key] for key in ('name', 'email')}, filter(lambda: entry: entry['age'] > 21, entries)))`
* **CSV**: See json

#### Select name and email from all users whose age is greater than 21 or whose first name starts with a 'J'
```
SELECT users(name,email){ WHERE(age > 21 | name ~= 'j%') }
```

* **MySQL**: `SELECT name, email FROM users WHERE age > 21 OR name LIKE 'j%'`
* **Mongo**: `db.users.find({$or:[{age:{$gt:21}}, {"name" /J.*/]}, {_id:0, name:1, email:1})`
* **JSON**: Something too complex for one line.
* **CSV**: See json.

## More examples
Here are some more examples of what can be done. Hopefully, the syntax is clear enough to figure out what the query is doing.

#### Create some users with float, date, and datetime data.
```
INSERT users {
    SET (
        name = "John",
        email = "john@mail.com",
        balance = 1234.00,
        rating = 5f,
        birthday = 1972-01-24,
        updated_at = 2020-08-30T13:33:55.77777
    )
}
```

#### Select where 2 conditions meet. Sort ascending and descending. 
```
SELECT users(id,name,rating) {
    WHERE (age > 18, rating > 1f),
    SORT(+name, -rating)
}
```

#### Aggregate
Aggregations will **always** summarize selected data into a list. Hence they are enclosed in [] and come after the main body.
```
SELECT users {
    WHERE (name ~= '%john%'| email ~= `%john%`),
}[count(*), count(birthday), avg(rating), sum(balance)]
```

#### Update some users
```
UPDATE users {
    WHERE(birthday > 1972-01-24),
    SET(age = 48, updated_at = 2020-08-30T13:33:55.77777)
}
```

#### delete some users
```
DELETE users { WHERE(email ~= '%spam.com') }
```
