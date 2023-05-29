from neo4j import GraphDatabase
from fastapi import FastAPI
from fastapi.responses import Response

app = FastAPI() # uvicorn main:app --reload
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "guifcm12"))

@app.get("/users")
def getAllUsers():
  with driver.session() as session:
      query = """
        MATCH (u:User)
        OPTIONAL MATCH (u)-[:Friend]->(f:User)
        RETURN u, COLLECT(f) AS friends;
      """
      result = session.run(query)
      return [ { **record['u'], 'friends': record['friends'] } for record in result ]

@app.post("/users")
def createUser(data: dict):
    if ('name' not in data or 'age' not in data): 
       return { 'message': 'É obrigatório informar: name e age' }
    
    with driver.session() as session:
       query = "MATCH (u:User {}) WHERE u.name = $name RETURN u;"
       result = session.run(query, name = data['name'])
       lenMatch = len([r for r in result])
       if lenMatch != 0: return Response(status_code=400)
       

       query = "CREATE (u:User {name: $name, age: $age}) RETURN u"
       result = session.run(query, data)
       return [ r['u'] for r in result ][0]
    
@app.post("/users/{userName}/add-friend")
def addFriend(userName: str, data: list):
   with driver.session() as session:
      query = """
        MATCH (u:User) WHERE u.name = $userName
        MATCH (f:User) WHERE f.name = $friendName 
        CREATE (u)-[:Friend]->(f);
      """
      for friend in data:
        session.run(query, userName = userName, friendName = friend)
      return Response(status_code=204)

@app.put("/users/{name}")
def updateUser(name: str, data: dict):
   with driver.session() as session:
      query = """
        MATCH (u:User {name: $findName})
        SET u.name = $name, 
            u.age = $age
        RETURN u;
      """
      result = session.run(query, findName = name, **data)
      return [ r['u'] for r in result ][0]
   
@app.delete("/users/{name}")
def deleteUser(name: str):
   with driver.session() as session:
      query = "MATCH (u:User {name: $findName}) DETACH DELETE u;"
      result = session.run(query, findName = name)
      return Response(status_code=204)