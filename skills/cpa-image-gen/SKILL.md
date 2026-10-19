---
name: cpa-image-gen
description: Generates real images through a locally configured OpenAI-compatible image gateway, saving the file and showing the picture in the conversation. Use whenever the user asks to draw or generate a picture, illustration, cover, wallpaper, avatar or poster, including casual Chinese phrasing such as 画一张图, 来张图, 帮我画, 画一下, 生成图片, 生成配图, 出图, 给我配一张图, 做个插画, 做张封面, 壁纸, 海报 or 画个头像. Also use when the user asks to restyle or rework an existing local image, such as 改成夜景, 换个风格, 变成水彩, since the gateway supports image-to-image through a reference file. Not for diagrams or charts, which belong to diagramming tools, not for writing image prompts for another service, and not for plain file conversion such as 转成 webp.
---

# CPA Image Generation

A local OpenAI-compatible gateway already serves an image model. One HTTP call costs about 30 seconds, so a written description is never a substitute for a requested picture.

## Setup

Gateway details stay out of this file. Copy `assets/config.template.json` to `config.json` beside this skill and fill it in. That file is gitignored, so installing the skill does not carry anyone's endpoint, model id or credential with it.

| Key | Meaning |
|---|---|
| `baseUrl` | Gateway root, the part before `/chat/completions` |
| `model` | Image-capable model id the gateway exposes |
| `outputDir` | Where generated files land by default |
| `apiKey` | Literal key, if you want it in this file |
| `apiKeyEnv` | Environment variable holding the key, used when `apiKey` is empty |
| `credentialsFile` + `credentialsKey` | Credential file and entry name to read the key from when neither above is set |
| `timeoutMs` | Request timeout, defaults to 120000 |

## Workflow

1. Turn the request into one vivid prompt. Keep the user's subject, style and mood, and add only what the image needs to render well, such as composition, lighting or framing.
2. Generate through the bundled script:

```bash
node ~/.dsh/skills/cpa-image-gen/scripts/generate.mjs "<prompt>" --out <absolute-path>.jpg
```

On Windows expand the home path, for example `D:/Users/<you>/.dsh/skills/cpa-image-gen/scripts/generate.mjs`. If the global shell rules require a prefix on external commands, put it in front of `node`. The script prints one JSON line `{ file, bytes, model, elapsed_ms }` on success.

3. Read the saved file with `read_image`. That step is what puts the picture into the conversation; a path alone leaves the user with nothing to look at.
4. Reply in the user's language with the image, then two short lines: the prompt you used, and the absolute file path. Skip step narration, because it competes with the picture for attention.

## Prompt patterns

A worked example. User says 帮我画一张江南雨天的小巷，竖版.

The prompt becomes: 雨后江南小巷，湿润泛光的青石板路向远处延伸，粉墙黛瓦与马头墙，木格窗，墙角青苔与盆栽，靠墙的油纸伞，雨雾中的石拱桥，写实电影感，9:16 portrait composition.

For an edit, pass the source file with `--ref` and describe only what changes while stating what must stay, for example 改成夜晚，屋檐暖黄灯笼为主光源，保留原有构图、透视与建筑结构，湿润石板路反射灯光，9:16 portrait composition. Naming what to preserve matters, because the model rewrites whatever the prompt leaves open.

Framing goes in the prompt as words. An explicit `size` field is ignored and the model falls back to its default wide output, so "1:1 square composition" or "9:16 portrait composition" is what actually changes the shape.

## Why these constraints

The gateway returns images only on `POST /v1/chat/completions`, as a data URI at `choices[0].message.images[0].image_url.url`, while `content` stays null. A null content field is normal here, not an empty response.

`/v1/responses` silently drops the image and leaves only a reasoning item, so a client speaking that protocol cannot see image output at all. For the same reason, never add this model to a chat-style model list that runs the responses protocol, because it will look like the model returns nothing.

Image-to-image works on the same endpoint: put the source file in the message as an `image_url` data URI alongside the text, which is what `--ref` does. The dedicated `/v1/images/generations` and `/v1/images/edits` routes may reject the model, since they serve a different model family. So rework existing images through chat completions, not through those routes.

Many hosted image models refuse requests from unsupported regions. When the gateway's egress is not proxied the call fails with `400 User location is not supported`, and text models fail the same way, so the fault is the egress path rather than the model. The gateway injects that proxy from its own configuration; the skill does not need to know the port.

## When the call fails

Each attempt costs about 30 seconds, so read the error instead of retrying with tweaked arguments.

- `missing gateway config` — `config.json` has not been created. Copy the template and fill it in.
- `gateway unreachable` — nothing is listening at `baseUrl`. The gateway process is not running.
- `User location is not supported` — egress is direct. The gateway's proxy setting is empty or that proxy is down, so report it instead of retrying.
- `no image in response` — the request reached a protocol that discards images, or the model id is wrong. Confirm chat completions and the `model` in `config.json`.
- HTTP 401 or `Missing API key` — the key is absent or invalid. Check the key source named in `config.json`, or pass `--key`.
- `cannot read reference image` — the `--ref` path is wrong or the file is unreadable.
- `gateway timed out` — the upstream stalled past the configured timeout. Retry once, then report.

## Flags

- `--out <file>` — destination; defaults to `outputDir` from the config.
- `--ref <image>` — source image for an edit; accepts png, jpeg, webp or gif and inlines it as a data URI.
- `--base <url>` — override `baseUrl` for one call.
- `--key <value>` — override the configured credential.
- `--model <id>` — override `model` for one call.

`CPA_IMAGE_GEN_CONFIG` points the script at a different config file, and `CPA_IMAGE_GEN_BASE` overrides the gateway root for a whole shell session.
