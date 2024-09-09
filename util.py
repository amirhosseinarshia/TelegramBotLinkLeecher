from telegram._files._basemedium import _BaseMedium
from telegram import Message

def extract_message_media(msg: Message) -> _BaseMedium:
    for attr in {'video', 'audio', 'voice', 'video_note', 'sticker', 'document', 'animation'}:
        if (medium := getattr(msg, attr, None)) is not None:
            return medium