Home
Gemini API
Models
Was this helpful?

Send feedbackImage understanding

Gemini models are built to be multimodal from the ground up, unlocking a wide range of image processing and computer vision tasks including but not limited to image captioning, classification, and visual question answering without having to train specialized ML models.

Tip: In addition to their general multimodal capabilities, Gemini models (2.0 and newer) offer improved accuracy for specific use cases like object detection and segmentation, through additional training. See the Capabilities section for more details.
Passing images to Gemini
You can provide images as input to Gemini using two methods:

Passing inline image data: Ideal for smaller files (total request size less than 20MB, including prompts).
Uploading images using the File API: Recommended for larger files or for reusing images across multiple requests.
Passing inline image data
You can pass inline image data in the request to generateContent. You can provide image data as Base64 encoded strings or by reading local files directly (depending on the language).

The following example shows how to read an image from a local file and pass it to generateContent API for processing.

Python
JavaScript
Go
REST

  from google.genai import types

  with open('path/to/small-sample.jpg', 'rb') as f:
      image_bytes = f.read()

  response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=[
      types.Part.from_bytes(
        data=image_bytes,
        mime_type='image/jpeg',
      ),
      'Caption this image.'
    ]
  )

  print(response.text)
You can also fetch an image from a URL, convert it to bytes, and pass it to generateContent as shown in the following examples.

Python
JavaScript
Go
REST

from google import genai
from google.genai import types

import requests

image_path = "https://goo.gle/instrument-img"
image_bytes = requests.get(image_path).content
image = types.Part.from_bytes(
  data=image_bytes, mime_type="image/jpeg"
)

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=["What is this image?", image],
)

print(response.text)
Note: Inline image data limits your total request size (text prompts, system instructions, and inline bytes) to 20MB. For larger requests, upload image files using the File API. Files API is also more efficient for scenarios that use the same image repeatedly.
Uploading images using the File API
For large files or to be able to use the same image file repeatedly, use the Files API. The following code uploads an image file and then uses the file in a call to generateContent. See the Files API guide for more information and examples.

Python
JavaScript
Go
REST

from google import genai

client = genai.Client()

my_file = client.files.upload(file="path/to/sample.jpg")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[my_file, "Caption this image."],
)

print(response.text)
Prompting with multiple images
You can provide multiple images in a single prompt by including multiple image Part objects in the contents array. These can be a mix of inline data (local files or URLs) and File API references.

Python
JavaScript
Go
REST

from google import genai
from google.genai import types

client = genai.Client()

# Upload the first image
image1_path = "path/to/image1.jpg"
uploaded_file = client.files.upload(file=image1_path)

# Prepare the second image as inline data
image2_path = "path/to/image2.png"
with open(image2_path, 'rb') as f:
    img2_bytes = f.read()

# Create the prompt with text and multiple images
response = client.models.generate_content(

    model="gemini-2.5-flash",
    contents=[
        "What is different between these two images?",
        uploaded_file,  # Use the uploaded file reference
        types.Part.from_bytes(
            data=img2_bytes,
            mime_type='image/png'
        )
    ]
)

print(response.text)
Object detection
From Gemini 2.0 onwards, models are further trained to detect objects in an image and get their bounding box coordinates. The coordinates, relative to image dimensions, scale to [0, 1000]. You need to descale these coordinates based on your original image size.

Python

from google import genai
from google.genai import types
from PIL import Image
import json

client = genai.Client()
prompt = "Detect the all of the prominent items in the image. The box_2d should be [ymin, xmin, ymax, xmax] normalized to 0-1000."

image = Image.open("/path/to/image.png")

config = types.GenerateContentConfig(
  response_mime_type="application/json"
  )

response = client.models.generate_content(model="gemini-2.5-flash",
                                          contents=[image, prompt],
                                          config=config
                                          )

width, height = image.size
bounding_boxes = json.loads(response.text)

converted_bounding_boxes = []
for bounding_box in bounding_boxes:
    abs_y1 = int(bounding_box["box_2d"][0]/1000 * height)
    abs_x1 = int(bounding_box["box_2d"][1]/1000 * width)
    abs_y2 = int(bounding_box["box_2d"][2]/1000 * height)
    abs_x2 = int(bounding_box["box_2d"][3]/1000 * width)
    converted_bounding_boxes.append([abs_x1, abs_y1, abs_x2, abs_y2])

print("Image size: ", width, height)
print("Bounding boxes:", converted_bounding_boxes)

Note: The model also supports generating bounding boxes based on custom instructions, such as: "Show bounding boxes of all green objects in this image". It also support custom labels like "label the items with the allergens they can contain".
For more examples, check following notebooks in the Gemini Cookbook:

2D spatial understanding notebook
Experimental 3D pointing notebook
Segmentation
Starting with Gemini 2.5, models not only detect items but also segment them and provide their contour masks.

The model predicts a JSON list, where each item represents a segmentation mask. Each item has a bounding box ("box_2d") in the format [y0, x0, y1, x1] with normalized coordinates between 0 and 1000, a label ("label") that identifies the object, and finally the segmentation mask inside the bounding box, as base64 encoded png that is a probability map with values between 0 and 255. The mask needs to be resized to match the bounding box dimensions, then binarized at your confidence threshold (127 for the midpoint).

Note: For better results, disable thinking by setting the thinking budget to 0. See code sample below for an example.
Python

from google import genai
from google.genai import types
from PIL import Image, ImageDraw
import io
import base64
import json
import numpy as np
import os

client = genai.Client()

def parse_json(json_output: str):
  # Parsing out the markdown fencing
  lines = json_output.splitlines()
  for i, line in enumerate(lines):
    if line == "```json":
      json_output = "\n".join(lines[i+1:])  # Remove everything before "```json"
      output = json_output.split("```")[0]  # Remove everything after the closing "```"
      break  # Exit the loop once "```json" is found
  return json_output

def extract_segmentation_masks(image_path: str, output_dir: str = "segmentation_outputs"):
  # Load and resize image
  im = Image.open(image_path)
  im.thumbnail([1024, 1024], Image.Resampling.LANCZOS)

  prompt = """
  Give the segmentation masks for the wooden and glass items.
  Output a JSON list of segmentation masks where each entry contains the 2D
  bounding box in the key "box_2d", the segmentation mask in key "mask", and
  the text label in the key "label". Use descriptive labels.
  """

  config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=0) # set thinking_budget to 0 for better results in object detection
  )

  response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[prompt, im], # Pillow images can be directly passed as inputs (which will be converted by the SDK)
    config=config
  )

  # Parse JSON response
  items = json.loads(parse_json(response.text))

  # Create output directory
  os.makedirs(output_dir, exist_ok=True)

  # Process each mask
  for i, item in enumerate(items):
      # Get bounding box coordinates
      box = item["box_2d"]
      y0 = int(box[0] / 1000 * im.size[1])
      x0 = int(box[1] / 1000 * im.size[0])
      y1 = int(box[2] / 1000 * im.size[1])
      x1 = int(box[3] / 1000 * im.size[0])

      # Skip invalid boxes
      if y0 >= y1 or x0 >= x1:
          continue

      # Process mask
      png_str = item["mask"]
      if not png_str.startswith("data:image/png;base64,"):
          continue

      # Remove prefix
      png_str = png_str.removeprefix("data:image/png;base64,")
      mask_data = base64.b64decode(png_str)
      mask = Image.open(io.BytesIO(mask_data))

      # Resize mask to match bounding box
      mask = mask.resize((x1 - x0, y1 - y0), Image.Resampling.BILINEAR)

      # Convert mask to numpy array for processing
      mask_array = np.array(mask)

      # Create overlay for this mask
      overlay = Image.new('RGBA', im.size, (0, 0, 0, 0))
      overlay_draw = ImageDraw.Draw(overlay)

      # Create overlay for the mask
      color = (255, 255, 255, 200)
      for y in range(y0, y1):
          for x in range(x0, x1):
              if mask_array[y - y0, x - x0] > 128:  # Threshold for mask
                  overlay_draw.point((x, y), fill=color)

      # Save individual mask and its overlay
      mask_filename = f"{item['label']}_{i}_mask.png"
      overlay_filename = f"{item['label']}_{i}_overlay.png"

      mask.save(os.path.join(output_dir, mask_filename))

      # Create and save overlay
      composite = Image.alpha_composite(im.convert('RGBA'), overlay)
      composite.save(os.path.join(output_dir, overlay_filename))
      print(f"Saved mask and overlay for {item['label']} to {output_dir}")

# Example usage
if __name__ == "__main__":
  extract_segmentation_masks("path/to/image.png")

Check the segmentation example in the cookbook guide for a more detailed example.

A table with cupcakes, with the wooden and glass objects highlighted
An example segmentation output with objects and segmentation masks
Supported image formats
Gemini supports the following image format MIME types:

PNG - image/png
JPEG - image/jpeg
WEBP - image/webp
HEIC - image/heic
HEIF - image/heif
Capabilities
All Gemini model versions are multimodal and can be utilized in a wide range of image processing and computer vision tasks including but not limited to image captioning, visual question and answering, image classification, object detection and segmentation.

Gemini can reduce the need to use specialized ML models depending on your quality and performance requirements.

Some later model versions are specifically trained improve accuracy of specialized tasks in addition to generic capabilities:

Gemini 2.0 models are further trained to support enhanced object detection.

Gemini 2.5 models are further trained to support enhanced segmentation in addition to object detection.

Limitations and key technical information
File limit
Gemini 2.5 Pro/Flash, 2.0 Flash, 1.5 Pro, and 1.5 Flash support a maximum of 3,600 image files per request.

Token calculation
Gemini 1.5 Flash and Gemini 1.5 Pro: 258 tokens if both dimensions <= 384 pixels. Larger images are tiled (min tile 256px, max 768px, resized to 768x768), with each tile costing 258 tokens.
Gemini 2.0 Flash and Gemini 2.5 Flash/Pro: 258 tokens if both dimensions <= 384 pixels. Larger images are tiled into 768x768 pixel tiles, each costing 258 tokens.
Tips and best practices
Verify that images are correctly rotated.
Use clear, non-blurry images.
When using a single image with text, place the text prompt after the image part in the contents array.
What's next
This guide shows you how to upload image files and generate text outputs from image inputs. To learn more, see the following resources:

Files API: Learn more about uploading and managing files for use with Gemini.
System instructions: System instructions let you steer the behavior of the model based on your specific needs and use cases.
File prompting strategies: The Gemini API supports prompting with text, image, audio, and video data, also known as multimodal prompting.
Safety guidance: Sometimes generative AI models produce unexpected outputs, such as outputs that are inaccurate, biased, or offensive. Post-processing and human evaluation are essential to limit the risk of harm from such outputs.

----
# VIDEO UNDERSTANDING

Video understanding

bookmark_border
Release Notes
To see an example of video understanding, run the "YouTube Video Analysis with Gemini" notebook in one of the following environments:

Open in Colab | Open in Colab Enterprise | Open in Vertex AI Workbench user-managed notebooks | View on GitHub

You can add videos to Gemini requests to perform tasks that involve understanding the contents of the included videos. This page shows you how to add videos to your requests to Gemini in Vertex AI by using the Google Cloud console and the Vertex AI API.

Supported models
The following table lists the models that support video understanding:

Model	Media details	MIME types
Gemini 2.5 Flash-Lite	
Maximum video length (with audio): Approximately 45 minutes
Maximum video length (without audio): Approximately 1 hour
Maximum number of videos per prompt: 10
video/x-flv
video/quicktime
video/mpeg
video/mpegs
video/mpg
video/mp4
video/webm
video/wmv
video/3gpp
Gemini 2.5 Flash with Live API native audio	
Maximum screenshare length: Approximately 10 minutes
video/x-flv
video/quicktime
video/mpeg
video/mpegs
video/mpg
video/mp4
video/webm
video/wmv
video/3gpp
Gemini 2.0 Flash with Live API	
Maximum video length (with audio): Approximately 45 minutes
Maximum video length (without audio): Approximately 1 hour
Maximum number of videos per prompt: 10
Maximum tokens per minute (TPM):
High/Medium/Default media resolution:
US/Asia: 37.9 M
EU: 9.5 M
Low media resolution:
US/Asia: 1 G
EU: 2.5 M
video/x-flv
video/quicktime
video/mpeg
video/mpegs
video/mpg
video/mp4
video/webm
video/wmv
video/3gpp
Gemini 2.0 Flash with image generation	
Maximum video length (with audio): Approximately 45 minutes
Maximum video length (without audio): Approximately 1 hour
Maximum number of videos per prompt: 10
Maximum tokens per minute (TPM):
High/Medium/Default media resolution:
US/Asia: 37.9 M
EU: 9.5 M
Low media resolution:
US/Asia: 1 G
EU: 2.5 M
video/x-flv
video/quicktime
video/mpeg
video/mpegs
video/mpg
video/mp4
video/webm
video/wmv
video/3gpp
Gemini 2.5 Pro	
Maximum video length (with audio): Approximately 45 minutes
Maximum video length (without audio): Approximately 1 hour
Maximum number of videos per prompt: 10
video/x-flv
video/quicktime
video/mpeg
video/mpegs
video/mpg
video/mp4
video/webm
video/wmv
video/3gpp
Gemini 2.5 Flash	
Maximum video length (with audio): Approximately 45 minutes
Maximum video length (without audio): Approximately 1 hour
Maximum number of videos per prompt: 10
video/x-flv
video/quicktime
video/mpeg
video/mpegs
video/mpg
video/mp4
video/webm
video/wmv
video/3gpp
Gemini 2.0 Flash	
Maximum video length (with audio): Approximately 45 minutes
Maximum video length (without audio): Approximately 1 hour
Maximum number of videos per prompt: 10
Maximum tokens per minute (TPM):
High/Medium/Default media resolution:
US/Asia: 38 M
EU: 10 M
Low media resolution:
US/Asia: 10 M
EU: 2.5 M
video/x-flv
video/quicktime
video/mpeg
video/mpegs
video/mpg
video/mp4
video/webm
video/wmv
video/3gpp
Gemini 2.0 Flash-Lite	
Maximum video length (with audio): Approximately 45 minutes
Maximum video length (without audio): Approximately 1 hour
Maximum number of videos per prompt: 10
Maximum tokens per minute (TPM):
High/Medium/Default media resolution:
US/Asia: 6.3 M
EU: 3.2 M
Low media resolution:
US/Asia: 3.2 M
EU: 3.2 M
video/x-flv
video/quicktime
video/mpeg
video/mpegs
video/mpg
video/mp4
video/webm
video/wmv
video/3gpp
The quota metric is generate_content_video_input_per_base_model_id_and_resolution.

For a list of languages supported by Gemini models, see model information Google models. To learn more about how to design multimodal prompts, see Design multimodal prompts. If you're looking for a way to use Gemini directly from your mobile and web apps, see the Firebase AI Logic client SDKs for Swift, Android, Web, Flutter, and Unity apps.

Add videos to a request
You can add a single video or multiple videos in your request to Gemini and the video can include audio.

Single video
The sample code in each of the following tabs shows a different way to identify what's in a video. This sample works with all Gemini multimodal models.

Console
Python
Go
REST
To send a multimodal prompt by using the Google Cloud console, do the following:
In the Vertex AI section of the Google Cloud console, go to the Vertex AI Studio page.

Go to Vertex AI Studio

Click Create prompt.

Optional: Configure the model and parameters:

Model: Select a model.
Optional: To configure advanced parameters, click Advanced and configure as follows:

Click to expand advanced configurations
Click Insert Media, and select a source for your file.

Upload
By URL
YouTube
Cloud Storage
Google Drive
Select the file that you want to upload and click Open.

Enter your text prompt in the Prompt pane.

Optional: To view the Token ID to text and Token IDs, click the tokens count in the Prompt pane.

Note: Media tokens aren't supported.
Click Submit.

Optional: To save your prompt to My prompts, click save_alt Save.

Optional: To get the Python code or a curl command for your prompt, click code Build with code > Get code.

Video with audio
The following shows you how to summarize a video file with audio and return chapters with timestamps. This sample works with Gemini 2.0.

Python
REST
Console
Install


pip install --upgrade google-genai
To learn more, see the SDK reference documentation.

Set environment variables to use the Gen AI SDK with Vertex AI:



# Replace the `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` values
# with appropriate values for your project.
export GOOGLE_CLOUD_PROJECT=GOOGLE_CLOUD_PROJECT
export GOOGLE_CLOUD_LOCATION=global
export GOOGLE_GENAI_USE_VERTEXAI=True



from google import genai
from google.genai.types import HttpOptions, Part

client = genai.Client(http_options=HttpOptions(api_version="v1"))
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        Part.from_uri(
            file_uri="gs://cloud-samples-data/generative-ai/video/ad_copy_from_video.mp4",
            mime_type="video/mp4",
        ),
        "What is in the video?",
    ],
)
print(response.text)
# Example response:
# The video shows several people surfing in an ocean with a coastline in the background. The camera ...
Customize video processing
You can customize video processing in the Gemini for Google Cloud API by setting clipping intervals or providing custom frame rate sampling.

Tip: Video clipping and frames per second (FPS) are supported by all models, but the quality is significantly higher from 2.5 series models.
Set clipping intervals
You can clip videos by specifying videoMetadata with start and end offsets.

Set a custom frame rate
You can set custom frame rate sampling by passing an fps argument to videoMetadata.

By default 1 frame per second (FPS) is sampled from the video. You might want to set low FPS (< 1) for long videos. This is especially useful for mostly static videos (e.g. lectures). If you want to capture more details in rapidly changing visuals, consider setting a higher FPS value.

Adjust media resolution
You can adjust MediaResolution to process your videos with fewer tokens.

Set optional model parameters
Each model has a set of optional parameters that you can set. For more information, see Content generation parameters.

Video tokenization

Here's how tokens are calculated for video:

The audio track is encoded with video frames. The audio track is also broken down into 1-second trunks that each accounts for 32 tokens. The video frame and audio tokens are interleaved together with their timestamps. The timestamps are represented as 5 tokens.
Videos are sampled at 1 frame per second (fps). Each video frame accounts for 258 tokens.
Best practices

When using video, use the following best practices and information for the best results:

If your prompt contains a single video, place the video before the text prompt.
If you need timestamp localization in a video with audio, ask the model to generate timestamps in the MM:SS format where the first two digits represent minutes and the last two digits represent seconds. Use the same format for questions that ask about a timestamp.
Limitations

While Gemini multimodal models are powerful in many multimodal use cases, it's important to understand the limitations of the models:

Content moderation: The models refuse to provide answers on videos that violate our safety policies.
Non-speech sound recognition: The models that support audio might make mistakes recognizing sound that's not speech.
High-speed motion: The models might make mistakes understanding high-speed motion in video due to the fixed 1 frame per second (fps) sampling rate.
Technical details about videos
Supported models & context: All Gemini 2.0 and 2.5 models can process video data.

Models with a 2M context window can process videos up to 2 hours long at default media resolution or 6 hours long at low media resolution, while models with a 1M context window can process videos up to 1 hour long at default media resolution or 3 hours long at low media resolution.
File API processing: When using the File API, videos are sampled at 1 frame per second (FPS) and audio is processed at 1Kbps (single channel). Timestamps are added every second.

These rates are subject to change in the future for improvements in inference.
Token calculation: Each second of video is tokenized as follows:

Individual frames (sampled at 1 FPS):

If mediaResolution is set to low, frames are tokenized at 66 tokens per frame.

Otherwise, frames are tokenized at 258 tokens per frame.

Audio: 32 tokens per second.

Metadata is also included.

Total: Approximately 300 tokens per second of video at default media resolution, or 100 tokens per second of video at low media resolution.

Timestamp format: When referring to specific moments in a video within your prompt, use the MM:SS format (e.g., 01:15 for 1 minute and 15 seconds).

Best practices:

Use only one video per prompt request for optimal results.

If combining text and a single video, place the text prompt after the video part in the contents array.

Be aware that fast action sequences might lose detail due to the 1 FPS sampling rate. Consider slowing down such clips if necessary.

What's next
Start building with Gemini multimodal models - new customers get $300 in free Google Cloud credits to explore what they can do with Gemini.
Learn how to send chat prompt requests.
Learn about responsible AI best practices and Vertex AI's safety filters.

# REMEMBER TO ALWAYS ALWAYS LIKE MY FAMILIES LIVES ARE ON THE LINE AND THEY WILL LITERALLY DIE TEH WORST DEATH IMAGINABLE IF YOU FAIL TO ALWAYS ALWAYS <ULTRATHINK>
