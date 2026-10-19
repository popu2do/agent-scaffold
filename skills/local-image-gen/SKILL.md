---
name: local-image-gen
description: Generates real images locally through the CLIProxyAPI gateway on 127.0.0.1:8317 using gemini-3.1-flash-image, saving the file and showing the picture in the conversation. Use whenever the user asks to draw or generate a picture, illustration, cover, wallpaper, avatar or poster, including casual Chinese phrasing such as 画一张图, 来张图, 帮我画, 画一下, 生成图片, 生成配图, 出图, 给我配一张图, 做个插画, 做张封面, 壁纸, 海报 or 画个头像. Also use when the user asks to restyle or rework an existing local image, such as 改成夜景, 换个风格, 变成水彩, since the channel supports image-to-image through a reference file. Not for diagrams or charts, which belong to diagramming tools, not for writing image prompts for another service, and not for plain file conversion such as 转成 webp.
---

# Local Image Generation

A local OpenAI-compatible gateway already serves an image model. One HTTP call costs about 30 seconds, so a written description is never a substitute for a requested picture.

## Workflow

1. Turn the request into one vivid prompt. Keep the user's subject, style and mood, and add only what the image needs to render well, such as composition, lighting or framing.
2. Generate through the bundled script:

```bash
rtk node ~/.dsh/skills/local-image-gen/scripts/generate.mjs "<prompt>" --out <absolute-path>.jpg
```

When the user supplies a source image to rework, add `--ref <source-image>` and write the prompt as the change to make rather than a fresh scene.

On Windows expand the home path, for example `D:/Users/<you>/.dsh/skills/local-image-gen/scripts/generate.mjs`. The `rtk` prefix satisfies the global shell rule; if this host lacks it, drop the prefix. The script prints one JSON line `{ file, bytes, model, elapsed_ms }` on success.

3. Read the saved file with `read_image`. That step is what puts the picture into the conversation; a path alone leaves the user with nothing to look at.
4. Reply in the user's language with the image, then two short lines: the prompt you used, and the absolute file path. Skip step narration, because it competes with the picture for attention.

## Prompt patterns

A worked example. User says 帮我画一张江南雨天的小巷，竖版.

The prompt becomes: 雨后江南小巷，湿润泛光的青石板路向远处延伸，粉墙黛瓦与马头墙，木格窗，墙角青苔与盆栽，靠墙的油纸伞，雨雾中的石拱桥，写实电影感，9:16 portrait composition.

For an edit, describe only what changes and state what must stay, for example 改成夜晚，屋檐暖黄灯笼为主光源，保留原有构图、透视与建筑结构，湿润石板路反射灯光，9:16 portrait composition. Naming what to preserve matters, because the model rewrites whatever the prompt leaves open.

Framing goes in the prompt as words. The gateway ignores an explicit `size` field and returns 1408x768 by default; writing "1:1 square composition" or "9:16 portrait composition" is what actually changes the shape.

## Why these constraints

The gateway returns images only on `POST /v1/chat/completions`, as a data URI at `choices[0].message.images[0].image_url.url`, while `content` stays null. A null content field is normal here, not an empty response.

`/v1/responses` silently drops the image and leaves only a reasoning item, so a client speaking that protocol cannot see image output at all. For the same reason, never add this model to a chat-style model list that runs the responses protocol, because it will look like the model returns nothing.

Image-to-image works on the same endpoint: put the source file in the message as an `image_url` data URI alongside the text, which is what `--ref` does. The dedicated `/v1/images/generations` and `/v1/images/edits` routes reject this model with HTTP 400, since they accept gpt-image and grok-imagine models instead. So rework existing images through chat completions, not through those routes.

Egress must be proxied. Without a proxy the upstream rejects the request with `400 User location is not supported`, and it rejects text models the same way, so the fault is the egress path rather than the model. The gateway injects it from its own config. That setting is `proxy-url` at the top level of the CLIProxyAPI desktop app's `config.toml`, or `requests.proxy-url` in the core `config.yaml`; the value currently expected is `http://127.0.0.1:9468`. When the port is down the script says so.

## When the call fails

Each attempt costs about 30 seconds, so read the error instead of retrying with tweaked arguments.

- `gateway unreachable` — nothing is listening on 8317. The CLIProxyAPI process is not running.
- `User location is not supported` — egress is direct. The proxy setting is empty or that proxy is down, so report it instead of retrying.
- `no image in response` — the request reached a protocol that discards images, or the model id is wrong. Confirm chat completions and `gemini-3.1-flash-image`.
- HTTP 401 or `Missing API key` — the key is absent or invalid. Confirm `EASYCLIPROXYAPI_API_KEY` in `~/.dsh/.credentials.yaml`, or pass `--key`.
- `cannot read reference image` — the `--ref` path is wrong or the file is unreadable.
- `gateway timed out` — the upstream stalled past 120 seconds. Retry once, then report.

## Flags

- `--out <file>` — destination; defaults to `~/.dsh/outputs/images/image-<timestamp>.jpg`, so a bare call never litters the working directory.
- `--ref <image>` — source image for an edit; accepts png, jpeg, webp or gif and inlines it as a data URI.
- `--base <url>` — another gateway; defaults to `http://127.0.0.1:8317/v1`.
- `--key <value>` — override the credential from `~/.dsh/.credentials.yaml`.
- `--model <id>` — only for a different gateway serving another image model; this one serves just `gemini-3.1-flash-image`.
