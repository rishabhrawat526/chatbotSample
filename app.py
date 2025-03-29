from flask import Flask,request,render_template,redirect,url_for,session
import os
import uuid

app=Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
UPLOADS_FOLDER="uploads"
os.makedirs(UPLOADS_FOLDER,exist_ok=True)


chat_memory={}
recent_history=[]
@app.before_request
def make_session_permanent():
    session.permanent=True
    if 'chat_id' not in session:
        session['chat_id'] = str(uuid.uuid4())

@app.route('/',methods=['GET','POST'])
def index():
    if request.method=="POST":
        pdf = request.files['pdf']
        if pdf:
            filepath = os.path.join(UPLOADS_FOLDER,pdf.filename)
            pdf.save(filepath)
            session['uploaded_pdf'] = filepath
            return redirect(url_for('after_upload'))
    return render_template('index.html')


@app.route('/after_upload')
def after_upload():
    return render_template('after_upload.html')


@app.route('/process_pdf',methods=['POST'])
def process_pdf():
    filepath=session.get('uploaded_pdf')
    if filepath:
        from rag_utils.pipeline import process_pdf_to_vectors
        process_pdf_to_vectors(filepath)
        return redirect(url_for('ask'))
    
    
@app.route('/ask',methods=['GET','POST'])
def ask():
    chat_id = session.get("chat_id")
    if chat_id not in chat_memory:
        chat_memory[chat_id]=[]

    
    answer=None
    if request.method =="POST":
        question = request.form['question']
        chat_memory[chat_id].append({'role':'user','content':question})
        from rag_utils.qa import answer_question
        recent_history = chat_memory[chat_id][-5:]
        answer = answer_question(question,recent_history)
        chat_memory[chat_id].append({'role':'assistant','content':answer})
        recent_history = chat_memory[chat_id][-5:]
        print(recent_history)
    return render_template('chat.html',history=chat_memory[chat_id])


if __name__=="__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT")) 
    )