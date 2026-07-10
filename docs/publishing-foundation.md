

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

## AI Variant Enhancer

Release Pack Y adds an enhancement endpoint for publishing variants.

Endpoint:

    POST /publishing/variants/{variant_id}/enhance

Modes:

- dry_run
- ollama

Dry-run mode is safe and does not require Ollama.

Ollama mode tries to rewrite the variant for the selected channel. If Ollama is unreachable, the backend falls back to a safe dry-run enhancement and records the error.

This step still does not publish anything.

## Publishing Review Workflow

Release Pack Z adds human review and approval for publishing variants.

Endpoint:

    PATCH /publishing/variants/{variant_id}/review

Review statuses:

- draft
- ready_for_review
- approved
- ready_for_publish
- rejected

The review workflow allows the operator to:

- compare source content with channel variant
- edit variant title
- edit variant body
- write review notes
- approve or reject a variant
- mark a variant as ready for publish

This still does not perform real publishing.

## WordPress Draft Connector

Release Pack AA adds the first real external publishing connector.

Endpoint:

    POST /publishing/variants/{variant_id}/wordpress/draft

Modes:

- dry_run
- wordpress

Dry-run mode does not send any request to WordPress.

WordPress mode creates a post with:

    status = draft

Required environment variables:

    DAMA_WORDPRESS_BASE_URL
    DAMA_WORDPRESS_USERNAME
    DAMA_WORDPRESS_APP_PASSWORD

Safety rules:

- No WordPress password is stored in the database.
- No token is entered through the frontend panel.
- Only approved / ready_for_publish WordPress variants can create drafts.
- Direct publish is not enabled.
