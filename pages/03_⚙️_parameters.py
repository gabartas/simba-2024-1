import streamlit as st
import parameters_functions

st.set_page_config(layout="wide")

if not "selectedID" in st.session_state:
        st.session_state["selectedID"] = 0

st.write("# activities parameters")

col1, col2, col3 = st.columns([0.2,0.6,0.2])



with col1 :
    st.write("### Main menu")
    if st.button("New activity", use_container_width=True):
        parameters_functions.newAssistant()

    if(st.session_state["selectedID"] != 0):
        st.write("### Activity menu")
        if st.button("Change name", use_container_width=True):
            parameters_functions.chgName(st.session_state["assistants"][st.session_state["selectedID"]])
        if st.button("Edit description", use_container_width=True):
            parameters_functions.descrEdit(st.session_state["assistants"][st.session_state["selectedID"]])
        if st.button("Change the activity's instructions", use_container_width=True):
            parameters_functions.chgPrompt(st.session_state["assistants"][st.session_state["selectedID"]])
        if st.button("Manage files", use_container_width=True):
            parameters_functions.manageFiles(st.session_state["assistants"][st.session_state["selectedID"]])
        if st.button("Delete this assistant", type="primary"):
            parameters_functions.delAssistant(st.session_state["assistants"][st.session_state["selectedID"]])

with col2 :
    st.write("### Selected activity")

    with st.container(border=True):
        if st.session_state["selectedID"] == 0:
            st.write("Please select an activity")
        else :
            assistant = st.session_state["assistants"][st.session_state["selectedID"]]
            st.write("**Name :**", assistant["name"])
            st.write("**Model :**", assistant["model"])
            st.write("**Description :**", assistant["description"])

            with st.expander("**Instructions :**"):
                st.text(assistant["instructions"])
            

with col3 :
    if "assistants" not in st.session_state:
        st.session_state["assistants"] = parameters_functions.getAssistants()    
    asdict = st.session_state["assistants"]
    st.write("### activities")
    if st.button("↺ refresh activities list"):
        st.session_state["assistants"] = parameters_functions.getAssistants() 
    if st.button("Cleanup files"):
        parameters_functions.delfiles()
    for id in asdict :
        if st.session_state["selectedID"] == id :
            t = "primary"
        else :
            t = "secondary"
        
        if st.button(label = asdict[id]["name"], type=t, use_container_width=True):
            st.session_state["selectedID"] = id
            st.rerun()