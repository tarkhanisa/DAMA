

# Publishing Foundation

Release Pack W adds the first layer of DAMA multi-channel publishing.

## What It Adds

- publishing channel service
- publishing API
- publishing frontend page
- channel creation form
- safe channel registry
- no real publishing yet

## Backend

Endpoints:

    GET /publishing/channels
    POST /publishing/channels
    GET /publishing/channels/{channel_id}
    PATCH /publishing/channels/{channel_id}
    POST /publishing/channels/{channel_id}/test

## Supported Channel Types

- wordpress
- telegram
- instagram
- linkedin
- whatsapp
- bale
- eitaa
- manual

## Safety

This foundation does not store secrets.

Do not enter:

- passwords
- access tokens
- API keys
- bot tokens
- application passwords

Secrets will be handled later through a safer configuration layer.

## Next Step

Release Pack X should add channel-specific content variants.

Example:

One master content asset becomes:

- WordPress post version
- Telegram message version
- Instagram caption version
- LinkedIn post version
- Manual review version

## Channel Variants

Release Pack X adds publishing variants.

A single content asset can now be adapted into channel-specific variants.

Endpoint:

    POST /publishing/variants/plan

Input:

- content_asset_id
- source_title
- source_body
- channel_ids

Output:

- one draft variant per selected channel

Current adaptation mode:

    rule_based

Future adaptation mode:

    ai_enhanced

No real publishing happens in this step.
