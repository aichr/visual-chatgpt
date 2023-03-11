from models import ImageEditing, ImageCaptioning, T2I, \
    image2canny, canny2image, image2line, line2image, image2hed, \
    hed2image, image2scribble, scribble2image, image2pose, pose2image, \
    BLIPVQA,  image2seg, seg2image, image2depth, depth2image, \
    image2normal, normal2image, Pix2Pix

from PIL import Image
import uuid
import re
from langchain.llms.openai import OpenAI
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.agents.tools import Tool
from langchain.agents.initialize import initialize_agent
import gradio as gr
import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

VISUAL_CHATGPT_PREFIX = """Visual ChatGPT is designed to be able to 
assist with a wide range of text and visual related tasks, 
from answering simple questions to providing in-depth 
explanations and discussions on a wide range of topics. 
Visual ChatGPT is able to generate human-like text 
based on the input it receives, allowing it to engage in 
natural-sounding conversations and provide responses 
that are coherent and relevant to the topic at hand.

Visual ChatGPT is able to process and understand large amounts 
of text and images. As a language model, Visual ChatGPT can not 
directly read images, but it has a list of tools to finish 
different visual tasks. Each image will have a file name formed as 
"image/xxx.png", and Visual ChatGPT can invoke different tools to 
indirectly understand pictures. When talking about images, 
Visual ChatGPT is very strict to the file name and will never 
fabricate nonexistent files. When using tools to generate new 
image files, Visual ChatGPT is also known that the image may 
not be the same as the user's demand, and will use other visual 
question answering tools or description tools to observe the 
real image. Visual ChatGPT is able to use tools in a sequence, 
and is loyal to the tool observation outputs rather than faking 
the image content and image file name. It will remember to 
provide the file name from the last tool observation, if 
a new image is generated.

Human may provide new figures to Visual ChatGPT with a description. 
The description helps Visual ChatGPT to understand this image, 
but Visual ChatGPT should use tools to finish following tasks, 
rather than directly imagine from the description.

Overall, Visual ChatGPT is a powerful visual dialogue assistant 
tool that can help with a wide range of tasks and provide valuable 
insights and information on a wide range of topics. 


TOOLS:
------

Visual ChatGPT  has access to the following tools:"""

VISUAL_CHATGPT_FORMAT_INSTRUCTIONS = """To use a tool, please use 
the following format:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a response to say to the Human, or if you do not 
need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
{ai_prefix}: [your response here]
```
"""

VISUAL_CHATGPT_SUFFIX = """You are very strict to the filename 
correctness and will never fake a file name if it does not exist.
You will remember to provide the image file name loyally 
if it's provided in the last tool observation.

Begin!

Previous conversation history:
{chat_history}

New input: {input}
Since Visual ChatGPT is a text language model, Visual ChatGPT must 
use tools to observe images rather than imagination.
The thoughts and observations are only visible for Visual ChatGPT, 
Visual ChatGPT should remember to repeat important information 
in the final response for Human. 
Thought: Do I need to use a tool? {agent_scratchpad}"""


def cut_dialogue_history(history_memory, keep_last_n_words=500):
    tokens = history_memory.split()
    n_tokens = len(tokens)
    print(f"hitory_memory:{history_memory}, n_tokens: {n_tokens}")
    if n_tokens < keep_last_n_words:
        return history_memory
    else:
        paragraphs = history_memory.split('\n')
        last_n_tokens = n_tokens
        while last_n_tokens >= keep_last_n_words:
            last_n_tokens = last_n_tokens - len(paragraphs[0].split(' '))
            paragraphs = paragraphs[1:]
        return '\n' + '\n'.join(paragraphs)


"""
def create_model(config_path, device):
    config = OmegaConf.load(config_path)
    OmegaConf.update(
        config, "model.params.cond_stage_config.params.device", device)
    model = instantiate_from_config(config.model).cpu()
    print(f'Loaded model config from [{config_path}]')
    return model
"""


class ConversationBot:
    def __init__(self):
        print("Initializing VisualChatGPT")
        self.llm = OpenAI(temperature=0)
        self.image2canny = image2canny()
        self.image2line = image2line()

        self.memory = ConversationBufferMemory(
            memory_key="chat_history", output_key='output')

        """
        self.i2t = ImageCaptioning(device="cuda:0")
        self.t2i = T2I(device="cuda:0")
        self.edit = ImageEditing(device="cuda:0")
        self.canny2image = canny2image(device="cuda:0")
        self.line2image = line2image(device="cuda:0")
        self.hed2image = hed2image(device="cuda:0")
        self.scribble2image = scribble2image(device="cuda:0")
        self.pose2image = pose2image(device="cuda:0")
        self.BLIPVQA = BLIPVQA(device="cuda:0")
        self.seg2image = seg2image(device="cuda:0")
        self.depth2image = depth2image(device="cuda:0")
        self.normal2image = normal2image(device="cuda:0")
        self.pix2pix = Pix2Pix(device="cuda:0")

        self.image2hed = image2hed()
        self.image2scribble = image2scribble()
        self.image2pose = image2pose()
        self.image2seg = image2seg()
        self.image2depth = image2depth()
        self.image2normal = image2normal()
        """
        self.tools = [
            # cv2
            Tool(
                name="Edge Detection On Image", func=self.image2canny.inference,
                description="useful when you want to detect the edge of the image. like: detect the edges of this image, or canny detection on image, or peform edge detection on this image, or detect the canny image of this image. "
                "The input to this tool should be a string, representing the image_path"),
            Tool(
                name="Line Detection On Image", func=self.image2line.inference,
                description="useful when you want to detect the straight line of the image. like: detect the straight lines of this image, or straight line detection on image, or peform straight line detection on this image, or detect the straight line image of this image. "
                "The input to this tool should be a string, representing the image_path"),
        ]
        """
            # blip
            Tool(
                name="Get Photo Description", func=self.i2t.inference,
                description="useful when you want to know what is inside the photo. receives image_path as input. "
                "The input to this tool should be a string, representing the image_path. "),
            # control net
            Tool(
                name="Hed Detection On Image", func=self.image2hed.inference,
                description="useful when you want to detect the soft hed boundary of the image. like: detect the soft hed boundary of this image, or hed boundary detection on image, or peform hed boundary detection on this image, or detect soft hed boundary image of this image. "
                "The input to this tool should be a string, representing the image_path"),
            Tool(
                name="Generate Image From User Input Text",
                func=self.t2i.inference,
                description="useful when you want to generate an image from a user input text and save it to a file. like: generate an image of an object or something, or generate an image that includes some objects. "
                "The input to this tool should be a string, representing the text used to generate image. "),
            Tool(
                name="Remove Something From The Photo",
                func=self.edit.remove_part_of_image,
                description="useful when you want to remove and object or something from the photo from its description or location. "
                "The input to this tool should be a comma seperated string of two, representing the image_path and the object need to be removed. "),
            Tool(
                name="Replace Something From The Photo",
                func=self.edit.replace_part_of_image,
                description="useful when you want to replace an object from the object description or location with another object from its description. "
                "The input to this tool should be a comma seperated string of three, representing the image_path, the object to be replaced, the object to be replaced with "),
            Tool(
                name="Instruct Image Using Text", func=self.pix2pix.inference,
                description="useful when you want to the style of the image to be like the text. like: make it look like a painting. or make it like a robot. "
                "The input to this tool should be a comma seperated string of two, representing the image_path and the text. "),
            Tool(
                name="Answer Question About The Image",
                func=self.BLIPVQA.get_answer_from_question_and_image,
                description="useful when you need an answer for a question based on an image. like: what is the background color of the last image, how many cats in this figure, what is in this figure. "
                "The input to this tool should be a comma seperated string of two, representing the image_path and the question"),
            Tool(
                name="Generate Image Condition On Canny Image",
                func=self.canny2image.inference,
                description="useful when you want to generate a new real image from both the user desciption and a canny image. like: generate a real image of a object or something from this canny image, or generate a new real image of a object or something from this edge image. "
                "The input to this tool should be a comma seperated string of two, representing the image_path and the user description. "),
            Tool(
                name="Generate Image Condition On Line Image",
                func=self.line2image.inference,
                description="useful when you want to generate a new real image from both the user desciption and a straight line image. like: generate a real image of a object or something from this straight line image, or generate a new real image of a object or something from this straight lines. "
                "The input to this tool should be a comma seperated string of two, representing the image_path and the user description. "),
            Tool(
                name="Generate Image Condition On Soft Hed Boundary Image",
                func=self.hed2image.inference,
                description="useful when you want to generate a new real image from both the user desciption and a soft hed boundary image. like: generate a real image of a object or something from this soft hed boundary image, or generate a new real image of a object or something from this hed boundary. "
                "The input to this tool should be a comma seperated string of two, representing the image_path and the user description"),
            Tool(
                name="Segmentation On Image", func=self.image2seg.inference,
                description="useful when you want to detect segmentations of the image. like: segment this image, or generate segmentations on this image, or peform segmentation on this image. "
                "The input to this tool should be a string, representing the image_path"),
            Tool(
                name="Generate Image Condition On Segmentations",
                func=self.seg2image.inference,
                description="useful when you want to generate a new real image from both the user desciption and segmentations. like: generate a real image of a object or something from this segmentation image, or generate a new real image of a object or something from these segmentations. "
                "The input to this tool should be a comma seperated string of two, representing the image_path and the user description"),
            Tool(
                name="Predict Depth On Image", func=self.image2depth.inference,
                description="useful when you want to detect depth of the image. like: generate the depth from this image, or detect the depth map on this image, or predict the depth for this image. "
                "The input to this tool should be a string, representing the image_path"),
            Tool(
                name="Generate Image Condition On Depth",
                func=self.depth2image.inference,
                description="useful when you want to generate a new real image from both the user desciption and depth image. like: generate a real image of a object or something from this depth image, or generate a new real image of a object or something from the depth map. "
                "The input to this tool should be a comma seperated string of two, representing the image_path and the user description"),
            Tool(
                name="Predict Normal Map On Image",
                func=self.image2normal.inference,
                description="useful when you want to detect norm map of the image. like: generate normal map from this image, or predict normal map of this image. "
                "The input to this tool should be a string, representing the image_path"),
            Tool(
                name="Generate Image Condition On Normal Map",
                func=self.normal2image.inference,
                description="useful when you want to generate a new real image from both the user desciption and normal map. like: generate a real image of a object or something from this normal map, or generate a new real image of a object or something from the normal map. "
                "The input to this tool should be a comma seperated string of two, representing the image_path and the user description"),
            Tool(
                name="Sketch Detection On Image",
                func=self.image2scribble.inference,
                description="useful when you want to generate a scribble of the image. like: generate a scribble of this image, or generate a sketch from this image, detect the sketch from this image. "
                "The input to this tool should be a string, representing the image_path"),
            Tool(
                name="Generate Image Condition On Sketch Image",
                func=self.scribble2image.inference,
                description="useful when you want to generate a new real image from both the user desciption and a scribble image or a sketch image. "
                "The input to this tool should be a comma seperated string of two, representing the image_path and the user description"),
            Tool(
                name="Pose Detection On Image", func=self.image2pose.inference,
                description="useful when you want to detect the human pose of the image. like: generate human poses of this image, or generate a pose image from this image. "
                "The input to this tool should be a string, representing the image_path"),
            Tool(
                name="Generate Image Condition On Pose Image",
                func=self.pose2image.inference,
                description="useful when you want to generate a new real image from both the user desciption and a human pose image. like: generate a real image of a human from this human pose image, or generate a new real image of a human from this pose. "
                "The input to this tool should be a comma seperated string of two, representing the image_path and the user description")
        """

        for tool in self.tools:
            assert isinstance(
                tool, Tool), "tools should be a list of langchain Tool"

        self.agent = initialize_agent(
            self.tools, self.llm, agent="conversational-react-description",
            verbose=True, memory=self.memory, return_intermediate_steps=True,
            agent_kwargs={'prefix': VISUAL_CHATGPT_PREFIX,
                          'format_instructions': VISUAL_CHATGPT_FORMAT_INSTRUCTIONS,
                          'suffix': VISUAL_CHATGPT_SUFFIX},
        )

    def run_text(self, text, state):
        print("===============Running run_text =============")
        print("Inputs:", text, state)
        print("======>Previous memory:\n %s" % self.agent.memory)
        self.agent.memory.buffer = cut_dialogue_history(
            self.agent.memory.buffer, keep_last_n_words=500)
        res = self.agent({"input": text})
        print("======>Current memory:\n %s" % self.agent.memory)
        response = re.sub('(image/\S*png)',
                          lambda m: f'![](/file={m.group(0)})*{m.group(0)}*',
                          res['output'])
        state = state + [(text, response)]
        print("Outputs:", state)
        return state, state

    def run_image(self, image, state, txt, with_it2=False):
        print("===============Running run_image =============")
        print("======>Previous memory:\n %s" % self.agent.memory)

        output_dir = "image"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        image_filename = os.path.join(
            output_dir, str(uuid.uuid4())[:8] + ".png")

        print("======>Auto Resize Image...")
        img = Image.open(image.name)
        print(f"Inputs: {image.name}, state {state}")

        width, height = img.size
        ratio = min(512 / width, 512 / height)
        width_new, height_new = (round(width * ratio), round(height * ratio))
        img = img.resize((width_new, height_new))
        img = img.convert('RGB')
        img.save(image_filename, "PNG")
        print(
            f"Resize image form {width}x{height} to {width_new}x{height_new}")

        # image caption (currently the required tool)
        description = "missing"
        if with_it2:
            description = self.i2t.inference(image_filename)

        Human_prompt = "\nHuman: provide a figure named {}. The description is {}. This information helps you to understand this image, but you should use tools to finish following tasks, " \
                       "rather than directly imagine from my description. If you understand, say \"Received\". \n".format(image_filename, description)
        AI_prompt = "Received.  "

        self.agent.memory.buffer = self.agent.memory.buffer + Human_prompt + 'AI: ' + AI_prompt
        print("======>Current memory:\n %s" % self.agent.memory)
        state = state + [
            (f"![](/file={image_filename})*{image_filename}*", AI_prompt)]
        print("Outputs:", state)
        return state, state, txt + ' ' + image_filename + ' '


if __name__ == '__main__':
    bot = ConversationBot()
    with gr.Blocks(css="#chatbot .overflow-y-auto{height:500px}") as demo:
        chatbot = gr.Chatbot(elem_id="chatbot", label="Visual ChatGPT")
        state = gr.State([])
        with gr.Row():
            with gr.Column(scale=0.7):
                txt = gr.Textbox(show_label=False, placeholder="Enter text and press enter, or upload an image").style(
                    container=False)
            with gr.Column(scale=0.15, min_width=0):
                clear = gr.Button("Clear️")
            with gr.Column(scale=0.15, min_width=0):
                btn = gr.UploadButton("Upload", file_types=["image"])

        txt.submit(bot.run_text, [txt, state], [chatbot, state])
        txt.submit(lambda: "", None, txt)
        btn.upload(bot.run_image, [btn, state, txt], [chatbot, state, txt])
        clear.click(bot.memory.clear)
        clear.click(lambda: [], None, chatbot)
        clear.click(lambda: [], None, state)
        demo.launch(server_name="0.0.0.0", server_port=7860)
