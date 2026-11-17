from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from app.engine import ConversationEngine,Session
app=FastAPI(title="Real-Time Voice Agent",version="0.1.0")
engine=ConversationEngine()
sessions:dict[str,Session]={}
class MessageRequest(BaseModel):
    text:str=Field(min_length=1,max_length=4000)
@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/sessions/{session_id}/messages")
def send_message(session_id:str,request:MessageRequest):
    session=sessions.setdefault(session_id,Session(session_id=session_id))
    try: answer=engine.reply(request.text,session.messages)
    except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    session.messages.extend([{"role":"user","content":request.text},{"role":"assistant","content":answer}])
    return {"session_id":session_id,"reply":answer,"message_count":len(session.messages)}
@app.get("/sessions/{session_id}")
def get_session(session_id:str):
    session=sessions.get(session_id)
    if session is None: raise HTTPException(status_code=404,detail="Session not found")
    return {"session_id":session_id,"messages":session.messages}
