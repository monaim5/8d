# TODO: all these functions should be defined on Chennel Model
def generate_title(title: str) -> str:
    return title + '(Exclusive)'


# return '"tag1", "tag2", "tag3"' of type str
def generate_tags(title: str) -> str:
    tags = title.split()
    additional_tags = []

    tags = '"' + '","'.join(tags) + '"'
    for tag in additional_tags:
        if len(tags.replace('"', '')) + len(tag) < 400:
            tags += f',"{tag.strip()}"'

    return tags


def generate_desc(title: str) -> str:
    desc = title
    return desc
