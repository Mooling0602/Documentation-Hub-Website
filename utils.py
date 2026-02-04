import sys

try:
    import runtime
except (ModuleNotFoundError, ImportError):
    runtime = None
from ruamel.yaml import YAML
from pathlib import Path
from typing import Literal

yaml = YAML(typ='safe')
replace_mode = Literal["i18n", "env"]


def get_languages(directory: str | Path) -> list[str]:
    """Get a support list of languages from target directory.

    :param directory: The target directory storaging yml language files.
    :return: A list of yml language filenames.
    """
    _dir = Path(directory) if isinstance(directory, str) else directory
    if not _dir.exists() or not _dir.is_dir():
        return []
    languages = []
    for i in _dir.iterdir():
        if not i.is_file():
            continue
        if i.suffix.lower() in ['.yml', '.yaml']:
            languages.append(i.name)
    languages.sort()
    return languages


def split_key_by_dot(key: str) -> list[str]:
    """Split a translation key to separated arguments.

    :param key: Translation key.
    :return: Separated arguments, will be used to search in the dict later.
    """
    if not key:
        return []
    else:
        key = key.strip()
        if not key:
            return []
    parts = [part.strip() for part in key.split('.') if part.strip()]
    return parts


def merge_args_to_key(*args) -> str:
    """Merge string arguments into a complete translation key string.

    :param args: String arguments you want to merge.
    :return: The translation key string.
    """
    processed_parts = []
    for i in args:
        if not isinstance(i, str):
            raise TypeError("Only strings are accepted!")
        part = str(i).strip().strip('.')
        if not part or part == "":
            continue
        processed_parts.append(part)
    return ".".join(processed_parts)


def get_template_text(mode: replace_mode, key: str) -> str:
    """Get template text for finding in target HTML file later.

    :param mode: Replacement mode.
    :param key: Translation or environment key.
    :return: Result of template text.
    """
    if (mode != "i18n") and (mode != "env"):
        raise TypeError("Invalid replace mode!")
    return f"{mode}:{key}"


def get_actual_content(key: str, data: dict[str, str], fallback: str) -> str:
    """Get actual text for replacing in target HTML file later.

    :param key: Translation or environment key.
    :param data: Optional, if you want to use custom dict instead of global one.
    :return: Result of actual text.
    """
    args = split_key_by_dot(key)
    try:
        for i in args:
            if isinstance(data, dict) and i in data:
                data = data[i]
            else:
                return fallback
        if isinstance(data, str):
            return data
        elif data is None:
            return fallback
        else:
            return str(data)
    except Exception as e:
        print(f"DBG: Error accessing key {key}: {e}")
        return fallback


def get_actual_env_content(key: str, data: dict[str, str] | None = None) -> str:
    """Get actual environment text for replacing in target HTML file later.

    :param key: Environment key.
    :param data: Optional, if you want to use custom dict instead of global one.
    :return: Result of actual text.
    """
    _fallback = get_template_text("env", key)
    _data = runtime.DATA_ENV
    if data:
        _data = data
    else:
        _data = _data.copy()
    return get_actual_content(key, _data, _fallback)


def get_actual_i18n_content(key: str, lang_file: str, data: dict[str, str] | None = None) -> str:
    """Get actual i18n text for replacing in target HTML file later.

    :param key: Translation key.
    :param lang_file: The target language file name.
    :param data: Optional, if you want to use custom dict instead of global one.
    :return: Result of actual text.
    """
    _fallback = get_template_text("i18n", key)
    _data = runtime.DATA_I18N[lang_file]
    if data:
        _data = data
    else:
        _data = _data.copy()
    return get_actual_content(key, _data, _fallback)


def load_data(file_path: Path | str) -> dict[str, str]:
    """Read data from target file path and return needed dict data.

    :param file_path: Target file path for reading data from.
    :return: Needed data.
    """
    file_path = Path(file_path) if isinstance(file_path, str) else file_path
    if not file_path.exists() or file_path.is_dir():
        raise TypeError("Target path should be a file.")
    if file_path.suffix.lower() not in ['.yml', '.yaml']:
        raise TypeError("Only YAML files are supported!")
    with open(file_path, 'r') as f:
        data = yaml.load(f)
    if data is not None:
        return data
    else:
        raise ValueError("Error reading data from target file path!")


def load_keys(file_path: Path | str) -> list[str]:
    path = Path(file_path) if isinstance(file_path, str) else file_path
    if not path.exists():
        raise FileNotFoundError()
    data = load_data(file_path)
    keys = []
    stack = [([], data)]
    while stack:
        key_path, key_data = stack.pop()
        for k, v in key_data.items():
            new_key_path = key_path + [k]
            if isinstance(v, dict):
                stack.append((new_key_path, v))
            else:
                if new_key_path:
                    processed_parts = []
                    for p in new_key_path:
                        if p is None:
                            continue
                        if p:
                            processed_parts.append(p)
                    key = merge_args_to_key(*processed_parts)
                    keys.append(key)
    unique_keys = []
    seen = set()
    for i in keys:
        if i not in seen:
            seen.add(i)
            unique_keys.append(i)
    unique_keys.sort()
    return unique_keys


def replace_text_in_file(file_path: Path | str, new_text: str, old_text: str, ignore_format_warning: bool = False):
    """Replace text in a file.

    :param file_path: Path to the target file.
    :param old_text: Text to be replaced.
    :param new_text: New text to replace with.
    :param ignore_format_warning: If True, ignore file format warnings.
    :return: True if replacement was successful, False otherwise.
    """
    path = Path(file_path) if isinstance(file_path, str) else file_path
    if not path.exists():
        print(f"Target file `{path}` not exists!")
        return
    if not ignore_format_warning and 'html' not in path.suffix.lower():
        print("WARN: The target file is not an HTMl file!")
        print("WARN: If you proceed, please ensure that the text file you're modifying will not cause any adverse effects after the changes.")
        print("Pass a boolean parameter set to True to confirm performing this action.")
        sys.exit(255)
    try:
        with open(path, 'r') as f:
            content = f.read()
        if old_text not in content:
            return
        new_content = content.replace(old_text, new_text)
        with open(path, 'w') as f:
            f.write(new_content)
    except PermissionError:
        print("ERR: Permission denied, check filesystem permissions.")


def get_string_removed_dot_and_after(string: str) -> str:
    index = string.find('.')
    if index <= 0:
        return ""
    return string[:index]













