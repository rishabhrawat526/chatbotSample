from flask import Flask,request,render_template,redirect,url_for,session
import os
import uuid

app=Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
UPLOADS_FOLDER="uploads"
os.makedirs(UPLOADS_FOLDER,exist_ok=True)

recent_history=[]

@app.before_request
def make_session_permanent():
    session.permanent=False
    if 'chat_id' not in session:
        session['chat_id'] = str(uuid.uuid4())
        session['chat_memory']=[]
    

@app.route('/',methods=['GET','POST'])
def index():
    print("Request args:", request.args)  # Debugging line

    if 'conversations' not in session:
        session['conversations']={}
    

    if request.args.get("new_chat") == "true":
        print("New chat detected!")  # Debugging print
        session['chat_memory']=[]
        # some logic will be added here
    if len(session['chat_memory']) > 0:
            print('yes this is running')
            return redirect(url_for('ask'))
    if request.method=="POST":
        pdf = request.files['pdf']
        if pdf:
            filepath = os.path.join(UPLOADS_FOLDER,pdf.filename)
            pdf.save(filepath)
            session['uploaded_pdf'] = filepath
            session['file_name'] = pdf.filename
            session['file_size']  = round(os.path.getsize(filepath) / 1024, 2)
            session['conversations'][pdf.filename]={'file_path':filepath,'file_name':pdf.filename,'chat_memory':[]}
            return redirect(url_for('after_upload'))
    return render_template('index.html',conversations = session.get('conversations',{}))


@app.route('/after_upload/')
def after_upload():
    file_name = session.get('file_name')
    return render_template('after_upload.html',file_name = file_name)



@app.route('/process_pdf',methods=['GET','POST'])
def process_pdf():
    filepath=session.get('uploaded_pdf')
    if filepath:
        from rag_utils.pipeline import process_pdf_to_vectors
        process_pdf_to_vectors(filepath)
        return redirect(url_for('ask'))
    
    
@app.route('/ask',methods=['GET','POST'])
def ask():
    chat_id = session.get("chat_id")
    file_name = session.get('file_name')
    file_size = session.get('file_size')
    
    answer=None
    if request.method =="POST":
        question = request.form['question']
        session['chat_memory'].append({'role':'user','content':question})
        from rag_utils.qa import answer_question
        recent_history = session['chat_memory'][-5:]
        answer = answer_question(question,recent_history)
        session['chat_memory'].append({'role':'assistant','content':answer})
        conversations = session.get('conversations')
        conversations[file_name]['chat_memory'] = session['chat_memory']
        print(recent_history)
    return render_template('chat.html',history=session['chat_memory'],file_name=file_name,file_size = file_size,conversations = session.get('conversations'),active_file = file_name)



@app.route('/load_conversation/<file_name>')
def load_conversation(file_name):
    print('load conversation method')
    print(file_name)
    session['file_name'] = file_name
    conversations = session.get('conversations')
    print(conversations)
    if file_name in conversations:
        filepath = conversations[file_name]['file_path']
        session['file_size']  = round(os.path.getsize(filepath) / 1024, 2)
        print(filepath)

        chat_mem = conversations[file_name]['chat_memory'] 
        print(chat_mem)
        session['uploaded_pdf'] = filepath
        session['chat_memory']=chat_mem
        return redirect(url_for('process_pdf'))
if __name__=="__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT")) 
    )