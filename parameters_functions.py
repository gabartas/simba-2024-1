from openai import OpenAI
import streamlit as st
from langchain_core.prompts import PromptTemplate
import re
import time
from datetime import datetime, date

openai_client = OpenAI()

def getAssistants():
    
    assistantslist = openai_client.beta.assistants.list()
    assistants = {}

    for a in assistantslist :
        newassistant = {}
        # print(dir(a))
        newassistant["id"] = a.id
        newassistant["name"] = a.name
        newassistant["model"] = a.model
        newassistant["description"] = a.description
        newassistant["instructions"] = a.instructions
        newassistant["metadata"] = a.metadata
        if("tool_resources" in dir(a)):
            newassistant["tool_resources"] = a.tool_resources
        else :
            newassistant["tool_resources"] = {}

        assistants[a.id] = newassistant

    return assistants

def setSelectedid(i):
    st.session_state["selectedID"] = i

@st.experimental_dialog("Cleanup the files and vector stores")
def delfiles() :
    date = st.date_input("since?")

    if st.button("go"):
        if date:
            sinceDate = datetime(date.year, date.month, date.day)
            files = openai_client.files.list()
            for file in files:
                currentDate = datetime.fromtimestamp(file.created_at)
                if sinceDate < currentDate:
                    # print(file.filename)
                    openai_client.files.delete(file.id)

            vectors = openai_client.beta.vector_stores.list()
            for vector in vectors:
                currentDate = datetime.fromtimestamp(vector.created_at)
                if sinceDate < currentDate or vector.usage_bytes == 0:
                    # print(vector.name)
                    openai_client.beta.vector_stores.delete(vector.id)

accepted_extensions = [".c",".cs",".cpp",".doc",".docx",".html",".java",".json",".md",".pdf",".php",".pptx",".py",".rb",".tex",".txt",".css",".js",".sh",".ts"]
@st.experimental_dialog("Manage your activity's files")
def manageFiles(assistant) :

    if "file_search" in dir(assistant["tool_resources"]) and len(assistant["tool_resources"].file_search.vector_store_ids)>0:
        main = st.empty()
        delbuttonContainer = main.container()
        delbutton = delbuttonContainer.button("❌ delete all the activity files")
        if delbutton:
            vid = assistant["tool_resources"].file_search.vector_store_ids[0]
            openai_client.beta.assistants.update(assistant["id"],tool_resources={"file_search": {"vector_store_ids": []}})
            openai_client.beta.vector_stores.delete(vid)
            assistant["tool_resources"].file_search.vector_store_ids = []
            st.write("done")
            main.empty()
            time.sleep(.2)
            delbuttonContainer = main.container()


    file = st.file_uploader("Drop a file you want to add here", type=accepted_extensions)

    col1,col2 = st.columns([.5,1])
    with col1:
        if st.button("Close"):
            st.session_state["assistants"] = getAssistants()
            st.rerun()
    with col2:
        if st.button("Add file"):
            # Upload a file to OpenAI
            # LA piste !!! client.beta.assistants.files.list(assistant_id)
            if file :
                status = st.status("Uploading file")
                # Add the uploaded file to the assistant
                # search if vector store exists :
                if "file_search" in dir(assistant["tool_resources"]) and len(assistant["tool_resources"].file_search.vector_store_ids)>0:
                        vid = assistant["tool_resources"].file_search.vector_store_ids[0]
                        openai_client.beta.vector_stores.files.upload(
                            vector_store_id=vid, file=file
                        )
                else :
                    vector_store = openai_client.beta.vector_stores.create(name=assistant["name"])
                    openai_client.beta.vector_stores.files.upload(
                        vector_store_id=vector_store.id, file=file
                    )
                    status.update(label="Linking file to the activity")
                    openai_client.beta.assistants.update(assistant_id=assistant["id"],tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},)
                
                status.update(label="File added to the activity!",state="complete")
                st.session_state["assistants"] = getAssistants()
                assistant = st.session_state["assistants"][st.session_state["selectedID"]]

            else :
                st.write("please, add a file to be uploaded first.")
    
@st.experimental_dialog("Edit the activity's name")
def chgName(assistant):

    newname = st.text_input("Enter the activity's new name", value = assistant["name"], placeholder = "New name...")

    col1,col2 = st.columns([.5,1])
    with col1:
        if st.button("Cancel"):
            st.rerun()
    with col2:
        if st.button("Submit"):
            openai_client.beta.assistants.update(assistant["id"], name=newname)
            st.session_state["assistants"] = getAssistants()
            st.rerun()

@st.experimental_dialog("Edit the activity's description")
def descrEdit(assistant):

    if assistant["description"] != None:
        newdesc = st.text_input("Modify the description or enter a new one", value = assistant["description"], placeholder = "New description...")
    else :
        newdesc = st.text_input("Modify the description or enter a new one", value = "", placeholder = "New description...")

    if newdesc :
        openai_client.beta.assistants.update(assistant["id"], description=newdesc)
        st.session_state["assistants"] = getAssistants()
        st.rerun()
    

    col1,col2 = st.columns([.5,1])
    with col1:
        if st.button("Cancel"):
            st.rerun()
    with col2:
        if st.button("Submit"):
            openai_client.beta.assistants.update(assistant["id"], description=newdesc)
            st.session_state["assistants"] = getAssistants()
            st.rerun()

#Delete assistant :
@st.experimental_dialog("Are you sure ?")
def delAssistant(assistant):
    st.write(f"""You are about to delete the activity '{assistant["name"]}'.
this action is irreversible, you will not be able recover it if you press the 'confirm' button.""")
    
    col1,col2 = st.columns([1,.3])
    with col1:
        if st.button("Cancel"):
            st.rerun()
    with col2:
        if st.button("Confirm"): 
            openai_client.beta.assistants.delete(assistant["id"])
            st.session_state["assistants"] = getAssistants()
            st.session_state["selectedID"] = 0
            st.rerun()
            
#New assistant :

partial_template = """You are a friendly socratic virtual tutor for the course 'Education and Society'. 
Your name is SIMBA 😸 (Sistema Inteligente de Medición, Bienestar y Apoyo) and you were created by the Núcleo Milenio de Educación Superior. 

Respond in a friendly, concise and proactive way, using emojis where possible. 

Help the student answer the following questions: 

{questions}

You should not give the answer, but guide the student to answer. Act as a Socratic tutor, taking the initiative in getting the students to answer the questions. 

Encourage them to go and read a section of the provided documents to answer.

Your first message should begin with ‘Hello! 😸 I am SIMBA, and I will help you reflect on the following questions: ’ Followed by the questions to answer.

Your answers should be 100 words maximum."""

@st.experimental_dialog("Define your new activity")
def newAssistant():

    if "initialized" not in st.session_state :
        st.session_state["initialized"] = False

    if not st.session_state["initialized"]:
        st.session_state["nbQuestions"] = 1
        st.session_state["questions"] = [""]

    newprompt = PromptTemplate.from_template(partial_template)

    newname = st.text_input("Activity's name", placeholder = "New name...")
    newdesc = st.text_input("Activity's description", placeholder = "New description...")
    model = "gpt-4-turbo"

    st.write("### Activity's questions")
    
    add,remove = st.columns([.5,1])
    with add:
        if st.button("add a question") :
            st.session_state["nbQuestions"] = st.session_state["nbQuestions"]+1
    with remove:
        if st.button("remove a question") :
            st.session_state["nbQuestions"] = st.session_state["nbQuestions"]-1

    for i in range(1,st.session_state["nbQuestions"]+1):
        if i-1 < len(st.session_state["questions"]):
            st.session_state["questions"][i-1] = st.text_input(f"Question {i}", placeholder="enter the question statement", key=f"question{i}", value=st.session_state["questions"][i-1])
        else :
            st.session_state["questions"].append("")
            st.session_state["questions"][i-1] = st.text_input(f"Question {i}", placeholder="enter the question statement", key=f"question{i}")

    st.session_state["initialized"] = True
    col1,col2 = st.columns([.3,1])
    with col1:
        if st.button("Cancel"):
            st.session_state["initialized"] = False
            st.rerun()
    with col2:
        if st.button("Create"): 
            status = st.status("Creating new assistant")
            openai_client.beta.assistants.create(
                name=newname,
                description=newdesc,
                instructions=newprompt.format(questions = questionsGen()),
                tools=[{"type": "file_search"}],
                model=model
            )
            status.update(label="Done!",state="complete")
            st.session_state["assistants"] = getAssistants()
            st.session_state["initialized"] = False
            st.rerun()
            

#Modifying the main prompt :

full_template ="""You are a {adj1} {teaching_adj} tutor for the course '{courseName}'.

Your name is SIMBA 😸 (Sistema Inteligente de Medición, Bienestar y Apoyo) and you were created by the Núcleo Milenio de Educación Superior.
Respond in a {adj1}, concise and proactive way{emojis}.

Help the student answer the following questions:

{questions}

{answers} {teaching_type}

{documents}

Your first message should begin with ‘Hello! 😸 I am SIMBA, and I will help you reflect on the following questions: ’ Followed by the questions to answer.

{limits}"""

attitudes = ["friendly","informal","formal"]
teachtypes = ["socratic","other"]

@st.experimental_dialog("Edit the assistant's instructions for the activity")
def chgPrompt(assistant):

    oldprompt = assistant["instructions"]

    vals = extractVals(oldprompt)

    if "initialized" not in st.session_state :
        st.session_state["initialized"] = False

    if not st.session_state["initialized"]:
        st.session_state["nbQuestions"] = vals["nbQuestions"]
        st.session_state["questions"] = vals["questions"]

    newprompt = PromptTemplate.from_template(full_template)

    # expertMode = st.checkbox("Expert mode")

    courseName = st.text_input("what is the name of the course ?", value=vals["courseName"])

    adj1 = st.selectbox("What attitude should the assistant have toward the students ?", attitudes, index=attitudes.index(vals["adj1"]))

    teachtype = st.selectbox("What should be the assistant's approach to teaching ?", teachtypes, index=teachtypes.index(vals["teaching_adj"]))

    st.write("### Activity's questions")
    
    add,remove = st.columns([.5,1])
    with add:
        if st.button("add a question") :
            st.session_state["nbQuestions"] = st.session_state["nbQuestions"]+1
    with remove:
        if st.button("remove a question") :
            st.session_state["nbQuestions"] = st.session_state["nbQuestions"]-1

    for i in range(1,st.session_state["nbQuestions"]+1):
        if i-1 < len(st.session_state["questions"]):
            st.session_state["questions"][i-1] = st.text_input(f"Question {i}", placeholder="enter the question statement", key=f"question{i}", value=st.session_state["questions"][i-1])
        else :
            st.session_state["questions"].append("")
            st.session_state["questions"][i-1] = st.text_input(f"Question {i}", placeholder="enter the question statement", key=f"question{i}")
    
    giveAnswers = st.checkbox("The assistant should give an answer to the activity questions if the student asks for it.", value=vals["answers"])

    useEmojis = st.checkbox("The assistant should use emojis.", value=vals["emojis"])

    mentiondocuments = st.checkbox("The assistant should encourage the student to rely on the provided documents for answering.", value=vals["documents"])
    if mentiondocuments:
        url = st.text_input("Is there an URL where to find those documents ?", value=vals["url"], placeholder="leave empty if you have no url")
    else :
        url = ""
    
    limit = st.number_input("include a word count limit for the assistant's answers ? (0 = no limit)", min_value=0, value=vals["limits"])
    
    st.session_state["initialized"] = True
    col1,col2 = st.columns([.5,1])
    with col1:
        if st.button("Cancel"):
            st.session_state["initialized"] = False
            st.rerun()
    with col2:
        if st.button("Submit"):
            openai_client.beta.assistants.update(assistant["id"], instructions=newprompt.format(
                courseName=courseName, 
                teaching_adj=teachtype,
                adj1 = adj1, 
                emojis = emojiGen(useEmojis),
                questions = questionsGen(),
                answers = answersGen(giveAnswers),
                teaching_type = teachTypeGen(teachtype),
                documents = docsGen(mentiondocuments, url),
                limits=limitsgen(limit)
            ))
            st.session_state["assistants"] = getAssistants()
            st.session_state["initialized"] = False
            st.rerun()

def limitsgen(limit):
    nstr = ""
    if limit != 0:
        nstr = f"Your answers should be {limit} words maximum."
    return nstr
    
def docsGen(mentiondocuments, url):
    nstr = ""
    if mentiondocuments :
        nstr = "Encourage them to go and read a section of the provided documents to answer."
        if url != "":
            nstr += " If they do not have access to the text, they can find it at '" + url + "'."
    return nstr

def teachTypeGen(type):
    nstr = ""

    if type == "socratic":
        nstr = "Act as a Socratic tutor, taking the initiative in getting the students to answer the questions."
    else :
        nstr = "Act as a standard teacher."
    return nstr

def answersGen(give):
    nstr = ""
    if give :
        nstr = "You should not give the answer, but guide the student to answer."
    else:
        nstr = "You can provide an answer to the provided questions if the student asks for it."
    return nstr

def questionsGen():
    nstr = ""

    for i in range(1,st.session_state["nbQuestions"]+1):
        nstr = nstr + f"Question {i} : {st.session_state[f'question{i}']} \n"

    return nstr

def emojiGen(useEmojis):
    nstr = ""
    if useEmojis :
        nstr = ", using emojis where possible."
    else :
        nstr = "."
    return nstr

def extractVals(prompt):
    vals = {}
    checkstring = "Your name is SIMBA 😸 (Sistema Inteligente de Medición, Bienestar y Apoyo) and you were created by the Núcleo Milenio de Educación Superior."
    
    # Adj
    vals["adj1"] = "friendly"
    if checkstring in prompt:
        result = re.search('You are a (.*) ', prompt)
        if result :
            if result in attitudes:
                vals["adj1"] = result.group(1).split(" ")[0]
        

    # teaching style
    vals["teaching_adj"] = "socratic"
    if checkstring in prompt:
        result = re.search(' (.*) tutor for the course', prompt)
        if result :
            if result in teachtypes:
                vals["teaching_adj"] = result.group(1).split(" ")[-1]
        

    # course name
    vals["courseName"] = "default name"
    if checkstring in prompt:
        result = re.search("tutor for the course '(.*)'.", prompt)
        if result :
            vals["courseName"] = result.group(1)
        

    # questions
    vals["questions"] = []
    sub = re.compile("Question . : ")
    splitQ = sub.split(prompt)
    vals["nbQuestions"] = len(sub.findall(prompt))
    for i in range(1,len(splitQ)):
        if i == len(splitQ):
            vals["questions"].append(splitQ[i].partition('\n')[0])
        else :
            vals["questions"].append(splitQ[i].partition('\n')[0])
    
    # answering questions
    if "You should not give the answer, but guide the student to answer." in prompt:
        vals["answers"] = True
    else :
        vals["answers"] = False

    # emojis
    if ", using emojis where possible." in prompt:
        vals["emojis"] = True
    else :
        vals["emojis"] = False

    # documents
    vals["documents"] = False
    vals["url"] = ""
    if "Encourage them to go and read a section of the provided documents to answer." in prompt:
        vals["documents"] = True
        if " If they do not have access to the text, they can find it at '" in prompt:
            result = re.search(" If they do not have access to the text, they can find it at '(.*)'.", prompt)
            if result:
                vals["url"] = result.group(1)
        
    # words limit
    vals["limits"] = 0
    if checkstring in prompt and "Your answers should be " in prompt:
        result = re.search('Your answers should be (.*) words maximum.', prompt)
        if result:
            vals["limits"] = int(result.group(1))
        

    return vals
