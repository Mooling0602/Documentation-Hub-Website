import runtime
import sys

from pathlib import Path
from utils import load_data, load_keys, get_languages, get_template_text, get_actual_env_content, replace_text_in_file, get_string_removed_dot_and_after, get_actual_i18n_content

LANG_LIST = []
LANG_FOLDER = Path("lang")
ENV_CFG = Path("env.yml")
HTML_TEMPLATE_FILE_NAME = "index.template.html"
HTML_TEMPLATE_FILE = Path(HTML_TEMPLATE_FILE_NAME)
HTML_COPIED_FILE_NAME = "index.html"
HTML_COPIED_FILE = Path(HTML_COPIED_FILE_NAME)


def on_load():
    env_cfg_status = "Err: no exists!"
    if ENV_CFG.exists():
        env_cfg_status = "ok."
    print(f"Checking env config: {env_cfg_status}")
    print("Detecting supported language files...")
    global LANG_LIST
    LANG_LIST = get_languages(LANG_FOLDER)
    for i in LANG_LIST:
        print(f"- {i}")
        runtime.DATA_I18N[i] = load_data(LANG_FOLDER / i)
        runtime.DATA_I18N_TRKEYS[i] = load_keys(LANG_FOLDER / i)
    runtime.DATA_ENV = load_data(ENV_CFG)
    runtime.DATA_ENV_KEYS = load_keys(ENV_CFG)
    print("Loaded actual texts.")


def on_user_input() -> str:
    global HTML_COPIED_FILE_NAME, HTML_COPIED_FILE
    user_input = input("Type language file name: ")
    if user_input not in LANG_LIST:
        print("The language file is not supported!")
        sys.exit(255)
    print(f"You selected language: {user_input}")
    HTML_COPIED_FILE_NAME = HTML_TEMPLATE_FILE_NAME.replace("template", get_string_removed_dot_and_after(user_input))
    HTML_COPIED_FILE = Path(HTML_COPIED_FILE_NAME)
    if Path(HTML_COPIED_FILE_NAME).exists():
        print("WARN: You will overriding a present HTML file!")
    HTML_TEMPLATE_FILE.copy(target=HTML_COPIED_FILE)
    return user_input


def main(lang_file: str):
    for i in runtime.DATA_ENV_KEYS:
        old_text = get_template_text("env", i)
        new_text = get_actual_env_content(i)
        replace_text_in_file(HTML_COPIED_FILE, new_text, old_text)
    print("Replaced environment texts!")
    i18n_keys = runtime.DATA_I18N_TRKEYS[lang_file]
    for i in i18n_keys:
        old_text = get_template_text("i18n", i)
        new_text = get_actual_i18n_content(i, lang_file)
        replace_text_in_file(HTML_COPIED_FILE, new_text, old_text)
    print("Replaced i18n texts!")


if __name__ == "__main__":
    on_load()
    lang_file = on_user_input()
    main(lang_file)
    print(f"Task finished! Output file is {HTML_COPIED_FILE}.")
    user_input = input("Rename to `index.html`? (N/y)")
    if user_input:
        if user_input.lower() == "y" or user_input.lower() == "yes":
            HTML_COPIED_FILE.move(HTML_COPIED_FILE.parent / "index.html")
