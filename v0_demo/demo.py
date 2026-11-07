from typing import Dict
import json
from textwrap import dedent
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import re
from datetime import datetime
from pptx import Presentation
from pptx.util import Inches
from gemini_genai import gen_image, gen_json_text, gen_text
def gen_outline(idea_prompt:str)->list[dict]:
    """generate outline of ppt, including optional parts and pages with title and points"""
    outline_prompt = dedent(f"""\
    You are a helpful assistant that generates an outline for a ppt.
    
    You can organize the content in two ways:
    
    1. Simple format (for short PPTs without major sections):
    [{{"title": "title1", "points": ["point1", "point2"]}}, {{"title": "title2", "points": ["point1", "point2"]}}]
    
    2. Part-based format (for longer PPTs with major sections):
    [
      {{
        "part": "Part 1: Introduction",
        "pages": [
          {{"title": "Welcome", "points": ["point1", "point2"]}},
          {{"title": "Overview", "points": ["point1", "point2"]}}
        ]
      }},
      {{
        "part": "Part 2: Main Content",
        "pages": [
          {{"title": "Topic 1", "points": ["point1", "point2"]}},
          {{"title": "Topic 2", "points": ["point1", "point2"]}}
        ]
      }}
    ]
    
    Choose the format that best fits the content. Use parts when the PPT has clear major sections.
    
    The user's request: {idea_prompt}. Now generate the outline, don't include any other text.
    
    """)
    outline = gen_json_text(outline_prompt)
    outline = json.loads(outline)
    return outline
    

def flatten_outline(outline: list[dict]) -> list[dict]:
    """partoutline"""
    pages = []
    for item in outline:
        if "part" in item and "pages" in item:
            # Config
            for page in item["pages"]:
                # Config
                page_with_part = page.copy()
                page_with_part["part"] = item["part"]
                pages.append(page_with_part)
        else:
            # Config
            pages.append(item)
    return pages

def gen_desc(idea_prompt, outline: list[Dict])->list[Dict] :
    """generate description for each page, including title, full text content and more ()"""
    # Config
    pages = flatten_outline(outline)
    
    # Config
    def generate_page_desc(i, page_outline):
        part_info = f"\nThis page belongs to: {page_outline['part']}" if 'part' in page_outline else ""
        desc_prompt = dedent(f"""\
        we are generating the text desciption for each ppt page.
        the original user request is: \n{idea_prompt}\n
        We already have the entire ouline: \n{outline}\n{part_info}
        Now please generate the description for page {i}:
        {page_outline}
        The description includes page title, text to render(keep it concise).
        For example:
        
        
        -  
        -  
        -  
        -  
        
        
        """)
        page_desc = gen_text(desc_prompt)
        # Config
        page_desc = dedent(page_desc)
        return (i, page_desc)  # 
    
    # Config
    desc_dict = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Config
        futures = [executor.submit(generate_page_desc, i, page_outline) 
                   for i, page_outline in enumerate(pages, 1)]
        
        # Config
        for future in as_completed(futures):
            i, page_desc = future.result()
            desc_dict[i] = page_desc
            print(f"✓  {i}/{len(pages)} ")
    
    # Config
    desc = [desc_dict[i] for i in sorted(desc_dict.keys())]
    return desc

def gen_outline_text(outline: list[Dict]) -> str:
    """outline"""
    text_parts = []
    for i, item in enumerate(outline, 1):
        if "part" in item and "pages" in item:
            text_parts.append(f"{i}. {item['part']}")
        else:
            text_parts.append(f"{i}. {item.get('title', 'Untitled')}")
    result = "\n".join(text_parts)
    # Config
    return dedent(result)

def gen_prompts(outline: list[Dict], desc: list[str]) -> list[str]:
    """"""
    pages = flatten_outline(outline)
    outline_text = gen_outline_text(outline)
    
    prompts = []
    for i, (page, page_desc) in enumerate(zip(pages, desc), 1):
        # Config
        if 'part' in page:
            current_section = page['part']
        else:
            current_section = f"{page.get('title', 'Untitled')}"
        
        # Config
        prompt = dedent(f"""\
        pptppt:
        {page_desc}
        
        ppt
        {outline_text}
        
        {current_section}
        
        4k 16:9.ppt
        """)
        print(f"\n-----\n prompt{i}:\n {prompt}\n-----\n")
        prompts.append(prompt)
    
    return prompts

def gen_images_parallel(prompts: list[str], ref_image: str, output_dir: str = "output") -> list[str]:
    """PPT"""
    # Config
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    def generate_single_image(i, prompt):
        """"""
        try:
            print(f"🎨  {i}/{len(prompts)} ...")
            image = gen_image(prompt, ref_image)
            if image:
                output_file = output_path / f"slide_{i:02d}.png"
                image.save(str(output_file))
                print(f"✓  {i}/{len(prompts)} : {output_file}")
                return (i, str(output_file))
            else:
                print(f"✗  {i}/{len(prompts)} ")
                return (i, None)
        except Exception as e:
            print(f"✗  {i}/{len(prompts)} : {e}")
            return (i, None)
    
    # Config
    image_files = {}
    with ThreadPoolExecutor(max_workers=8) as executor:  # 3API
        # Config
        futures = [executor.submit(generate_single_image, i, prompt) 
                   for i, prompt in enumerate(prompts, 1)]
        
        # Config
        for future in as_completed(futures):
            i, image_file = future.result()
            image_files[i] = image_file
    
    # Config
    return [image_files[i] for i in sorted(image_files.keys())]

def create_pptx_from_images(input_dir: str = "output", output_file: str = "presentation.pptx"):
    """
    slide_XX.pngPPTX
    
    Args:
        input_dir: 
        output_file: PPTX
    """
    input_path = Path(input_dir)
    slide_files = list(input_path.glob("slide_*.png"))
    
    def extract_number(filename):
        match = re.search(r'slide_(\d+)', filename.stem)
        return int(match.group(1)) if match else 0
    
    slide_files.sort(key=extract_number)
    
    print(f"\n📁  {len(slide_files)} ")
    print(f"📝  PPTX ...")
    
    # Config
    prs = Presentation()
    
    # Config
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(5.625)
    
    # Config
    for i, image_file in enumerate(slide_files, 1):
        print(f"  ✓  {i} : {image_file.name}")
        
        # Config
        blank_slide_layout = prs.slide_layouts[6]  # 6
        slide = prs.slides.add_slide(blank_slide_layout)
        
        # Config
        # Config
        slide.shapes.add_picture(
            str(image_file),
            left=0,
            top=0,
            width=prs.slide_width,
            height=prs.slide_height
        )
    
    # Config
    prs.save(output_file)
    
    print(f"\n✅  PPTX : {output_file}")
    print(f"📊  {len(slide_files)} ")
    return True

def gen_ppt(idea_prompt, ref_image):
    # Config
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"output_{timestamp}"
    pptx_filename = f"presentation_{timestamp}.pptx"
    
    print(f"📂 : {output_dir}")
    print(f"📄 PPTX: {pptx_filename}\n")
    
    outline = gen_outline(idea_prompt)
    
    # Config
    print("PPT Outline:")
    for item in outline:
        if "part" in item and "pages" in item:
            print(f"\n{item['part']}")
            for j, page in enumerate(item["pages"], 1):
                print(f"  Page {j}: {page.get('title', 'Untitled')}")
                print(f"    Points: {page.get('points', [])}")
        else:
            print(f"\nPage: {item.get('title', 'Untitled')}")
            print(f"  Points: {item.get('points', [])}")
    
    # Config
    desc = gen_desc(idea_prompt, outline)
    
    # Config
    pages = flatten_outline(outline)
    for i, (page, page_desc) in enumerate(zip(pages, desc), 1):
        part_tag = f"[{page['part']}] " if 'part' in page else ""
        print(f"-----\nPage {i} {part_tag}- {page.get('title', 'Untitled')}\n-----")
        print(f"{page_desc}\n")
    
    # Config
    print("...")
    prompts = gen_prompts(outline, desc)
    print(f"✓  {len(prompts)} \n")
    
    # Config
    print("PPT...")
    image_files = gen_images_parallel(prompts, ref_image, output_dir)
    
    # Config
    print("PPT")
    successful = [f for f in image_files if f is not None]
    print(f"✓  {len(successful)}/{len(image_files)} ")
    for i, image_file in enumerate(image_files, 1):
        if image_file:
            print(f"   {i}: {image_file}")
        else:
            print(f"   {i}: ")
    
    # Config
    if successful:
        print("PPTX...")
        create_pptx_from_images(output_dir, pptx_filename)
    
    return image_files
    
    

if __name__ == "__main__":
    idea_prompt="ppt.3"
    ref_image="template_g.png"
    gen_ppt(idea_prompt, ref_image)