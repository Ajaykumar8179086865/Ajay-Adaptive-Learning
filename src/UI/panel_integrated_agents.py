import autogen
import panel as pn
import os
import asyncio
import json
from src import globals
#from src.Agents.agents import *
from src.UI.avatar import avatar
os.environ["AUTOGEN_USE_DOCKER"] = "0"

globals.input_future = None
from ..Agents.base_agent import MyBaseAgent
from ..Agents.conversable_agent import MyConversableAgent
from ..Agents.student_agent import StudentAgent
from ..Agents.knowledge_tracer_agent import KnowledgeTracerAgent
from ..Agents.teacher_agent import TeacherAgent
from ..Agents.tutor_agent import TutorAgent
from ..Agents.problem_generator_agent import ProblemGeneratorAgent
from ..Agents.solution_verifier_agent import SolutionVerifierAgent
from ..Agents.programmer_agent import ProgrammerAgent
from ..Agents.code_runner_agent import CodeRunnerAgent
from ..Agents.learner_model_agent import LearnerModelAgent
from ..Agents.level_adapter_agent import LevelAdapterAgent
from ..Agents.motivator_agent import MotivatorAgent
from src.Agents.group_chat_manager_agent import CustomGroupChatManager

# Global variables
script_dir = os.path.dirname(os.path.abspath(__file__))
progress_file_path = os.path.join(script_dir, '../../progress.json')

# Initialize agents
student = StudentAgent(
    human_input_mode='ALWAYS', 
    description = """ 
            You are StudentAgent, a system proxy for a human user. 
            Your primary role is to facilitate communication between the human and the educational system. 
            When the human provides input or requests information, you will relay these to the appropriate agent. 
            Maintain clarity and accuracy in all communications to enhance the human's learning experience
            """,
    system_message = "Student"
)    

knowledge_tracer = KnowledgeTracerAgent(
    human_input_mode='ALWAYS',
    description="""You are a Knowledge Tracer.
                    You test the student on what they know.
                    You work with the Problem Generator to present problems to the Student.
                    You work with the Learner Model to keep track of the Student's level.""",
    system_message="Knowledge Tracer"
)
teacher = TeacherAgent(
    human_input_mode='NEVER',
    description="""You are a Teacher.
                    When asked by the Student to learn new material, you present clear and concise lecture-type material.""",
    system_message="Teacher"
)
tutor = TutorAgent(
    human_input_mode='NEVER',
    description="""TutorAgent is designed to assist students in real-time with their math problems. 
                    It offers solutions and explanations, responding effectively to inquiries to support adaptive learning.""",
    system_message="Tutor"
)
problem_generator = ProblemGeneratorAgent(
    human_input_mode='NEVER',
    description="""ProblemGenerator is designed to generate mathematical problems based on the current curriculum and the student's learning level.
                    ProblemGenerator ensures that the problems generated are appropriate and challenging.""",
    system_message="Problem Generator"
)
solution_verifier = SolutionVerifierAgent(
    human_input_mode='ALWAYS',
    description="""SolutionVerifierAgent ensures the accuracy of solutions provided for various problems. 
                    SolutionVerifierAgent checks solutions against the correct answers and offers feedback on their correctness.""",
    system_message="Solution Verifier"
)
programmer = ProgrammerAgent()
code_runner = CodeRunnerAgent(
    human_input_mode='NEVER',
    description="""Code Runner specializes in executing and displaying code outputs. 
                    It interacts seamlessly with educational and development agents, enhancing learning and programming experiences.""",
    system_message="Code Runner"
)
learner_model = LearnerModelAgent(
    human_input_mode='ALWAYS',
    description="""Learner Model assesses the Student's educational journey, adapting learning paths by collaborating with the Tutor and Knowledge Tracer. 
                    It analyzes performance data to provide feedback, help set educational goals, and adjust the difficulty of tasks.""",
    system_message="Learner Model"
)
level_adapter = LevelAdapterAgent(
    human_input_mode='NEVER',
    description="""LevelAdapter interacts with the Learner Model to fetch information about the Student's learning progress.
                    It provides input to other agents or systems based on the Student's level.""",
    system_message="Level Adapter"
)
motivator = MotivatorAgent(
    human_input_mode='NEVER',
    description="""Motivator provides positive and encouraging feedback to the Student to keep them motivated.
                    It offers specific praise and acknowledges the Student's effort and progress.""",
    system_message="Motivator"
)

# Dictionary of all agents
agents_dict = {
    "student": student,
    "knowledge_tracer": knowledge_tracer,
    "teacher": teacher,
    "tutor": tutor,
    "problem_generator": problem_generator,
    "solution_verifier": solution_verifier,
    "programmer": programmer,
    "code_runner": code_runner,
    "learner_model": learner_model,
    "level_adapter": level_adapter,
    "motivator": motivator
}

# Set up group chat and manager
TRANSITIONS = 'DISALLOWED'      # Set TRANSITIONS for type
if TRANSITIONS == 'DISALLOWED':

    disallowed_agent_transitions = {
        student: [solution_verifier, programmer, code_runner, learner_model, level_adapter, motivator],
        tutor: [programmer, code_runner],
        teacher: [knowledge_tracer, problem_generator, solution_verifier, programmer, code_runner, learner_model, level_adapter, motivator],
        knowledge_tracer: [teacher, tutor, motivator],
        problem_generator: [teacher, solution_verifier, programmer, code_runner, motivator],
        solution_verifier: [student, teacher, problem_generator, learner_model, level_adapter, motivator],
        programmer: [student, tutor, teacher, knowledge_tracer, learner_model, level_adapter, motivator],
        code_runner: [student, teacher, tutor, knowledge_tracer, problem_generator, learner_model, level_adapter, motivator],
        learner_model: [student, teacher, problem_generator, solution_verifier, programmer, code_runner],
        level_adapter: [student, teacher, solution_verifier, programmer, code_runner, motivator],
        motivator: [tutor, teacher, knowledge_tracer, problem_generator, solution_verifier, programmer, code_runner, learner_model, level_adapter]
    }
    groupchat = autogen.GroupChat(agents=list(agents_dict.values()), 
                                messages=[],
                                max_round=40,
                                send_introductions=True,
                                speaker_transitions_type="disallowed",
                                allowed_or_disallowed_speaker_transitions=disallowed_agent_transitions,
                                )
    
elif TRANSITIONS == 'ALLOWED':
    allowed_agent_transitions = {
        student: [tutor],
        tutor: [student, teacher, problem_generator, solution_verifier, motivator],
        teacher: [student, tutor, learner_model],
        knowledge_tracer: [student, problem_generator, learner_model, level_adapter],
        problem_generator: [tutor],
        solution_verifier: [programmer],
        programmer: [code_runner],
        code_runner: [tutor, solution_verifier],
        learner_model: [knowledge_tracer, level_adapter],
        level_adapter: [tutor, problem_generator, learner_model],
        motivator: [tutor]
    }
    groupchat = autogen.GroupChat(agents=list(agents_dict.values()), 
                              messages=[],
                              max_round=40,
                              send_introductions=True,
                              speaker_transitions_type="allowed",
                              allowed_or_disallowed_speaker_transitions=allowed_agent_transitions,
                               )

else:  # Unconstrained
    agents = list(agents_dict.values()) # All agents
    groupchat = autogen.GroupChat(agents=agents, 
                              messages=[],
                              max_round=40,
                              send_introductions=True,
                              )
manager = CustomGroupChatManager(filename=progress_file_path, groupchat=groupchat)


# Function to create the Panel application
def create_app():
    pn.extension(design="material")

    async def callback(contents: str, user: str, instance: pn.chat.ChatInterface):
        if not globals.initiate_chat_task_created:
            asyncio.create_task(manager.delayed_initiate_chat(tutor, manager, contents))
        else:
            if globals.input_future and not globals.input_future.done():
                globals.input_future.set_result(contents)
            else:
                print("No input being awaited.")

    chat_interface = pn.chat.ChatInterface(callback=callback)
    chat_interface.messages = []  # Ensure messages attribute is initialized correctly

    def print_messages(recipient, messages, sender, config):
        content = messages[-1]['content']
        chat_interface.messages.append(content)  # Append new message to messages attribute
        chat_interface.send(content, user=messages[-1].get('name', recipient.name), avatar=avatar.get(messages[-1]['name'], None), respond=False)
        return False, None

    for agent in groupchat.agents:
        agent.chat_interface = chat_interface
        agent.register_reply([autogen.Agent, None], reply_func=print_messages, config={"callback": None})

    app = pn.template.BootstrapTemplate(title=globals.APP_NAME)
    app.main.append(
        pn.Column(
            chat_interface
        )
    )

    # Load chat history on startup
    chat_history_messages = manager.get_messages_from_json()  # Corrected method call
    if chat_history_messages:
        manager.resume(chat_history_messages)
        for message in chat_history_messages:
            if 'exit' not in message:
                chat_interface.messages.append(message["content"])  # Append chat history to messages attribute
                chat_interface.send(
                    message["content"],
                    user=message.get("role", None),
                    avatar=avatar.get(message.get("role", None), None),
                    respond=False
                )
        chat_interface.send("Time to continue your studies!", user="System", respond=False)
    else:
        chat_interface.send("Welcome to the Adaptive Math Tutor! How can I help you today?", user="System", respond=False)

    return app

if __name__ == "__main__":
    app = create_app()
    pn.serve(app)