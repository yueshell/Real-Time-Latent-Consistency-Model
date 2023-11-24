from diffusers import DiffusionPipeline, AutoencoderTiny, LCMScheduler
from compel import Compel
import torch

try:
    import intel_extension_for_pytorch as ipex  # type: ignore
except:
    pass

import psutil
from config import Args
from pydantic import BaseModel, Field
from PIL import Image
from pipelines.utils.translate import translate

base_model = "/content/models/LCM/SimianLuo/LCM_Dreamshaper_v7"
taesd_model = "madebyollin/taesd"
scheduler = LCMScheduler.from_pretrained(
    "/content/models/LCM/SimianLuo/LCM_Dreamshaper_v7/scheduler/scheduler_config.json")

default_prompt = "Portrait of The Terminator with , glare pose, detailed, intricate, full of colour, cinematic lighting, trending on artstation, 8k, hyperrealistic, focused, extreme details, unreal engine 5 cinematic, masterpiece"


class Pipeline:
    class Info(BaseModel):
        name: str = "txt2img"
        title: str = "Text-to-Image LCM"
        description: str = "Generates an image from a text prompt"
        input_mode: str = "text"

    class InputParams(BaseModel):
        prompt: str = Field(
            default_prompt,
            title="Prompt",
            field="textarea",
            id="prompt",
        )
        seed: int = Field(
            2159232, min=0, title="Seed", field="seed", hide=True, id="seed"
        )
        steps: int = Field(
            4, min=2, max=15, title="Steps", field="range", hide=True, id="steps"
        )
        width: int = Field(
            512, min=2, max=15, title="Width", disabled=True, hide=True, id="width"
        )
        height: int = Field(
            512, min=2, max=15, title="Height", disabled=True, hide=True, id="height"
        )
        guidance_scale: float = Field(
            8.0,
            min=1,
            max=30,
            step=0.001,
            title="Guidance Scale",
            field="range",
            hide=True,
            id="guidance_scale",
        )

    def __init__(self, args: Args, device: torch.device, torch_dtype: torch.dtype):
        if args.safety_checker:
            self.pipe = DiffusionPipeline.from_pretrained(base_model,scheduler=scheduler)
        else:
            self.pipe = DiffusionPipeline.from_pretrained(
                base_model, safety_checker=None,scheduler=scheduler
            )
        if args.use_taesd:
            self.pipe.vae = AutoencoderTiny.from_pretrained(
                taesd_model, torch_dtype=torch_dtype, use_safetensors=True
            )

        self.pipe.set_progress_bar_config(disable=True)
        self.pipe.to(device=device, dtype=torch_dtype)
        if device.type != "mps":
            self.pipe.unet.to(memory_format=torch.channels_last)

        # check if computer has less than 64GB of RAM using sys or os
        if psutil.virtual_memory().total < 64 * 1024**3:
            self.pipe.enable_attention_slicing()

        if args.torch_compile:
            self.pipe.unet = torch.compile(
                self.pipe.unet, mode="reduce-overhead", fullgraph=True
            )
            self.pipe.vae = torch.compile(
                self.pipe.vae, mode="reduce-overhead", fullgraph=True
            )

            self.pipe(prompt="warmup", num_inference_steps=1, guidance_scale=8.0)

        self.compel_proc = Compel(
            tokenizer=self.pipe.tokenizer,
            text_encoder=self.pipe.text_encoder,
            truncate_long_prompts=False,
        )

    def predict(self, params: "Pipeline.InputParams") -> Image.Image:
        generator = torch.manual_seed(params.seed)
        autotranslate = False
        global translate_text
        if autotranslate:
            translate_text = translate(params.prompt)
            print(translate_text)
        else:
            translate_text = params.prompt
        prompt_embeds = self.compel_proc(translate_text)
        results = self.pipe(
            prompt_embeds=prompt_embeds,
            generator=generator,
            num_inference_steps=params.steps,
            guidance_scale=params.guidance_scale,
            width=params.width,
            height=params.height,
            output_type="pil",
        )
        nsfw_content_detected = (
            results.nsfw_content_detected[0]
            if "nsfw_content_detected" in results
            else False
        )
        if nsfw_content_detected:
            return None
        return results.images[0]
