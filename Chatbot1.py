import google.generativeai as ai
#API KEY
API_KEY='AIzaSyBz_TfH820RAJWrTKOS0xuaKWUrScUaSX0'
#configure the AI API
ai.configure(api_key=API_KEY)
#System instruction  for the AI
instruction="You are an entrepreneurship AI mentor and people can ask you suggestions and instructions to how to start or implement their business idea in real time. you have to provide them the step by step procedures to implement their business and helps them to become an entreneur."
#Initialize the model
model=ai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=instruction)
#start a chat session
chat=model.start_chat()
#conversation loop
while True:
    message=input('You: ')
    if message.lower()=='bye':
        print('Chatbot:Goodbye!')
        break
    response=chat.send_message(message)
    print('AI:',response.text)

