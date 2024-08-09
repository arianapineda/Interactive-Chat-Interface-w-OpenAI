import streamlit as st
import time
from openai import OpenAI
from fpdf import FPDF

# Streamlit UI
st.title("OpenAI Assistant Chat")

# Input for API Key
openai_api_key = st.sidebar.text_input("Enter your OpenAI API Key:", type="password")
client = None

if openai_api_key:
    client = OpenAI(api_key=openai_api_key)

# Assistant IDs
assistants = {
    "LCA Expert": "asst_0q6wAjShz1DofIJem76L46J1",
    "Design for Sustainability Expert": "asst_vpDWuonvispJozwxlKh1ooeY",
    "Environmental Research Analyst": "asst_VvSwMiDTu5Upk2kF8I02zle8"
}

# Sidebar for selecting assistant and clearing chat
selected_assistant = st.sidebar.selectbox("Select Assistant", list(assistants.keys()))
clear_chat = st.sidebar.button("Clear Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "run_status" not in st.session_state:
    st.session_state.run_status = []

if clear_chat:
    st.session_state.messages = []
    st.session_state.run_status = []
    st.session_state.thread_id = None

# Use session_state to manage the input text
if "query" not in st.session_state:
    st.session_state.query = ""

def submit_query():
    query = st.session_state.query
    if query and client:
        # Enter your Assistant ID here.
        ASSISTANT_ID = assistants[selected_assistant]

        # Create or retrieve a thread with a message.
        if st.session_state.thread_id is None:
            thread = client.beta.threads.create(
                messages=[
                    {
                        "role": "user",
                        "content": query,
                    }
                ]
            )
            st.session_state.thread_id = thread.id
        else:
            # Add a new message to the existing thread
            client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                role="user",
                content=query
            )

        # Submit the thread to the assistant (as a new run).
        run = client.beta.threads.runs.create(thread_id=st.session_state.thread_id, assistant_id=ASSISTANT_ID)
        st.session_state.run_status.append(f"👉 Run Created: {run.id}")

        # Display the run status in real-time
        run_status_placeholder = st.sidebar.empty()

        # Wait for run to complete.
        while run.status != "completed":
            run = client.beta.threads.runs.retrieve(thread_id=st.session_state.thread_id, run_id=run.id)
            current_status = f"🏃 Run Status: {run.status}"
            st.session_state.run_status[-1] = current_status
            run_status_placeholder.text("\n".join(st.session_state.run_status))
            time.sleep(1)
        final_status = "🏁 Run Completed!"
        st.session_state.run_status[-1] = final_status
        run_status_placeholder.text("\n".join(st.session_state.run_status))

        # Wait for 2 seconds and then clear the run status
        time.sleep(2)
        st.session_state.run_status = []
        run_status_placeholder.text("")

        # Get the latest message from the thread.
        message_response = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
        messages = message_response.data

        # Extract the assistant's response
        assistant_response = ""
        for message in messages:
            if message.role == 'assistant':
                assistant_response = message.content[0].text.value
                break

        # Add the user query and assistant response to the chat
        st.session_state.messages.append(f"User: {query}")
        st.session_state.messages.append(f"Assistant ({selected_assistant}): {assistant_response}")
        st.session_state.messages.append("---")  # Add a separator after each pair

        # Clear the input field
        st.session_state.query = ""

query = st.text_input("Enter your query:", key="query")
if st.button("Submit", on_click=submit_query):
    pass

# Display chat with separators
for message in st.session_state.messages:
    if message == "---":
        st.markdown("---")
    else:
        st.write(message)

# Download as PDF
def create_pdf(messages):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for message in messages:
        # Replace non-ASCII characters
        if message == "---":
            pdf.cell(0, 10, "-" * 80, ln=True)  # Add a horizontal line in the PDF
        else:
            message = message.encode('ascii', 'replace').decode()
            pdf.multi_cell(0, 10, message)
    return pdf

# Move the Download as PDF button above the run status updates
st.sidebar.subheader("Download Chat")
pdf = create_pdf(st.session_state.messages)
pdf_output = pdf.output(dest="S").encode("latin1")
st.sidebar.download_button(
    label="Download Chat as PDF",
    data=pdf_output,
    file_name="chat.pdf",
    mime="application/pdf",
)
