"""Instagram and Facebook publishing operations."""

from __future__ import annotations

import json

from .graph import GraphClient, GraphError


def publish_instagram(graph: GraphClient, ig_user_id: str, plan: dict) -> dict:
    caption = plan["instagram_caption"]
    images = plan["images"]

    if len(images) == 1:
        image = images[0]
        container = graph.post(f"{ig_user_id}/media", {
            "image_url": image["url"],
            "caption": caption,
            "alt_text": _alt(image),
        })
        published = graph.post(f"{ig_user_id}/media_publish", {"creation_id": container["id"]})
        media_id = published["id"]
    else:
        children = []
        for image in images:
            item = graph.post(f"{ig_user_id}/media", {
                "image_url": image["url"],
                "is_carousel_item": "true",
                "alt_text": _alt(image),
            })
            children.append(item["id"])

        container = graph.post(f"{ig_user_id}/media", {
            "media_type": "CAROUSEL",
            "children": ",".join(children),
            "caption": caption,
        })
        published = graph.post(f"{ig_user_id}/media_publish", {"creation_id": container["id"]})
        media_id = published["id"]

    return {
        "media_id": media_id,
        "permalink": _permalink(graph, media_id),
    }


def publish_facebook(graph: GraphClient, page_id: str, plan: dict, include_alt: bool = True) -> dict:
    photo_ids = []
    for image in plan["images"]:
        params = {
            "url": image["url"],
            "published": "false",
        }
        if include_alt and image.get("alt"):
            params["alt_text_custom"] = image["alt"][:1000]
        photo = graph.post(f"{page_id}/photos", params)
        photo_ids.append(photo["id"])

    attached = json.dumps([{"media_fbid": photo_id} for photo_id in photo_ids])
    post = graph.post(f"{page_id}/feed", {
        "message": plan["facebook_caption"],
        "attached_media": attached,
    })
    post_id = post["id"]
    return {
        "post_id": post_id,
        "photo_ids": photo_ids,
        "permalink": _permalink(graph, post_id),
    }


def publish_comment(graph: GraphClient, object_id: str, text: str) -> dict:
    comment = graph.post(f"{object_id}/comments", {"message": text})
    return {"comment_id": comment.get("id")}


def _alt(image: dict) -> str:
    return (image.get("alt") or "")[:1000]


def _permalink(graph: GraphClient, object_id: str) -> str | None:
    try:
        info = graph.get(object_id, {"fields": "permalink"})
        return info.get("permalink")
    except GraphError:
        try:
            info = graph.get(object_id, {"fields": "permalink_url"})
            return info.get("permalink_url")
        except GraphError:
            return None
