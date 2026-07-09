from pathlib import Path

ROOT = Path("I:/DAMA")

target = ROOT / "frontend/src/components/generate-content-form.tsx"

target.write_text(
r'''
"use client";

import { FormEvent, useMemo, useState } from "react";

type ProjectOption = {
  id: string;
  name: string;
  status?: string;
  project_type?: string;
};

type ContentTypeOption = {
  key: string;
  label: string;
  description?: string;
};

type ModelOption = {
  name: string;
  provider?: string;
};

type GenerateContentFormProps = {
  apiBaseUrl: string;
  projects: ProjectOption[];
  contentTypes: ContentTypeOption[];
  models: ModelOption[];
};

type GenerationResult = {
  ok: boolean;
  endpoint: string;
  raw: unknown;
  outputText: string;
  assetId?: string;
  message?: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function getNestedString(source: unknown, keys: string[]): string {
  let current: unknown = source;

  for (const key of keys) {
    const record = asRecord(current);
    current = record[key];
  }

  return typeof current === "string" ? current : "";
}

function extractOutput(payload: unknown): string {
  const directKeys = [
    "response",
    "content",
    "text",
    "output",
    "result",
    "body",
    "generated_content",
    "generated_text",
    "message"
  ];

  const record = asRecord(payload);

  for (const key of directKeys) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) {
      return value;
    }
  }

  const nestedCandidates = [
    ["saved_content_asset", "body"],
    ["saved_content_asset", "response"],
    ["saved_content_asset", "content"],
    ["asset", "body"],
    ["asset", "response"],
    ["content_asset", "body"],
    ["content_asset", "response"],
    ["data", "body"],
    ["data", "response"],
    ["data", "content"],
    ["data", "text"],
    ["generation", "response"],
    ["generation", "content"],
    ["generation", "text"]
  ];

  for (const candidate of nestedCandidates) {
    const value = getNestedString(payload, candidate);
    if (value.trim()) {
      return value;
    }
  }

  return JSON.stringify(payload, null, 2);
}

function extractAssetId(payload: unknown): string | undefined {
  const record = asRecord(payload);
  const directKeys = ["asset_id", "content_asset_id", "id"];

  for (const key of directKeys) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) {
      return value;
    }
  }

  const nestedCandidates = [
    ["saved_content_asset", "id"],
    ["asset", "id"],
    ["content_asset", "id"],
    ["data", "asset_id"],
    ["data", "content_asset_id"],
    ["data", "id"]
  ];

  for (const candidate of nestedCandidates) {
    const value = getNestedString(payload, candidate);
    if (value.trim()) {
      return value;
    }
  }

  return undefined;
}

async function postJson(
  endpoint: string,
  payload: Record<string, unknown>
): Promise<{ ok: boolean; status: number; data: unknown }> {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  let data: unknown;

  try {
    data = await response.json();
  } catch {
    data = await response.text();
  }

  return {
    ok: response.ok,
    status: response.status,
    data
  };
}

function defaultProjectContext(projectName: string): string {
  const normalized = projectName.toLowerCase();

  if (normalized.includes("gorgoran") || normalized.includes("گرگران")) {
    return `افسانه گرگران یک پروژه انیمیشن/ترنس‌مدیاست. ایده اصلی آن بازخوانی تازه‌ای از قصه شنگول و منگول از زاویه جهان گرگ‌هاست. این پروژه باید حرفه‌ای، سینمایی، کودک‌ونوجوان‌پسند، خانوادگی و قابل ارائه به سرمایه‌گذار معرفی شود. شخصیت و جهان داستان مهم است. از متن سطحی، ایموجی، شعارهای عمومی و جمله‌های کلیشه‌ای پرهیز شود.`;
  }

  if (normalized.includes("urma") || normalized.includes("اورما")) {
    return `اورماشاپ هاب معرفی و راهنمای خرید محصولات کاربردی خانه و آشپزخانه است. لحن باید ساده، قابل اعتماد، مصرف‌کننده‌محور و مناسب فروش آنلاین باشد. متن باید به کاربرد واقعی محصول، انتخاب بهتر و تجربه آرام‌تر در خانه کمک کند.`;
  }

  if (normalized.includes("damamedia") || normalized.includes("دامامدیا")) {
    return `دامامدیا یک پلتفرم و مجموعه خلاق برای تولید، مدیریت و توسعه محتوای هوشمند، پروژه‌های انیمیشن، رسانه، وب و محصولات ترنس‌مدیا است. لحن باید حرفه‌ای، روشن، اجرایی و قابل ارائه باشد.`;
  }

  return "";
}

function buildQualityBrief(input: {
  projectName: string;
  projectContext: string;
  contentType: string;
  outputLanguage: string;
  purpose: string;
  audience: string;
  tone: string;
  outputFormat: string;
  qualityLevel: string;
  title: string;
  brief: string;
}) {
  return `
نقش شما:
شما یک نویسنده و استراتژیست محتوای حرفه‌ای برای دامامدیا هستید.

مهم:
خروجی باید متن نهایی قابل استفاده باشد، نه توضیح درباره روند کار.

زبان خروجی:
${input.outputLanguage}

نام پروژه:
${input.projectName}

اطلاعات ضروری پروژه:
${input.projectContext || "اطلاعات تکمیلی پروژه در brief آمده است."}

نوع محتوا:
${input.contentType}

عنوان پیشنهادی:
${input.title || "در صورت نیاز، یک عنوان دقیق و مناسب پیشنهاد بده."}

هدف محتوا:
${input.purpose}

مخاطب:
${input.audience}

لحن:
${input.tone}

قالب خروجی:
${input.outputFormat}

سطح کیفیت:
${input.qualityLevel}

قوانین کیفیت:
- از ایموجی استفاده نکن، مگر کاربر صریحاً خواسته باشد.
- از عبارت‌های سطحی مثل «به وبسایت ما خوش آمدید» استفاده نکن، مگر کاربر صریحاً خواسته باشد.
- از دعوت‌های بی‌معنی مثل «برای اطلاعات بیشتر تماس بگیرید» پرهیز کن، مگر برای متن تبلیغاتی لازم باشد.
- متن باید خاص همین پروژه باشد، نه یک متن عمومی قابل استفاده برای هر پروژه.
- اگر اطلاعات کافی نیست، با احتیاط بنویس و جزئیات ساختگی اضافه نکن.
- ادعای بزرگ، آمار، جایزه، موفقیت یا همکاری واقعی جعل نکن.
- متن باید فارسی طبیعی و غیرترجمه‌ای باشد، اگر زبان خروجی فارسی است.
- ساختار متن باید تمیز، قابل کپی و آماده استفاده باشد.
- از کلی‌گویی، تکرار و جمله‌های تزئینی بی‌محتوا پرهیز کن.
- خروجی را مستقیم شروع کن؛ مقدمه‌ای مثل «در ادامه متن پیشنهادی...» ننویس.
- اگر قالب خروجی متن سایت است، متن باید برای سایت قابل استفاده باشد، نه کپشن اینستاگرام.
- اگر نوع محتوا اشتباهاً social caption بود اما brief متن سایت خواست، نیاز brief را در اولویت قرار بده.

درخواست اصلی کاربر:
${input.brief}
`.trim();
}

export function GenerateContentForm({
  apiBaseUrl,
  projects,
  contentTypes,
  models
}: GenerateContentFormProps) {
  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const [contentType, setContentType] = useState(contentTypes[0]?.key ?? "");
  const [model, setModel] = useState(models[0]?.name ?? "");
  const [title, setTitle] = useState("");
  const [brief, setBrief] = useState("");
  const [outputLanguage, setOutputLanguage] = useState("فارسی");
  const [purpose, setPurpose] = useState("متن حرفه‌ای و قابل استفاده برای سایت یا ارائه");
  const [audience, setAudience] = useState("مخاطب عمومی، سرمایه‌گذار یا کارفرمای بالقوه");
  const [tone, setTone] = useState("حرفه‌ای، روشن، سینمایی، جذاب و غیراغراق‌آمیز");
  const [outputFormat, setOutputFormat] = useState("متن منظم با تیتر کوتاه و چند پاراگراف قابل استفاده");
  const [qualityLevel, setQualityLevel] = useState("کیفیت بالا، آماده استفاده، خاص پروژه، بدون کلی‌گویی");
  const [projectContext, setProjectContext] = useState(
    projects[0]?.name ? defaultProjectContext(projects[0].name) : ""
  );
  const [saveOutput, setSaveOutput] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<GenerationResult | null>(null);
  const [error, setError] = useState("");

  const selectedProject = projects.find((project) => project.id === projectId);
  const selectedContentType = contentTypes.find((type) => type.key === contentType);

  const canSubmit = useMemo(() => {
    return Boolean(projectId && contentType && brief.trim() && !isGenerating);
  }, [brief, contentType, isGenerating, projectId]);

  function handleProjectChange(nextProjectId: string) {
    setProjectId(nextProjectId);
    const nextProject = projects.find((project) => project.id === nextProjectId);

    if (nextProject) {
      const suggestedContext = defaultProjectContext(nextProject.name);
      if (suggestedContext) {
        setProjectContext(suggestedContext);
      }
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!canSubmit) {
      setError("اول پروژه، نوع محتوا و توضیح کار را وارد کن.");
      return;
    }

    setIsGenerating(true);
    setError("");
    setResult(null);

    const enhancedBrief = buildQualityBrief({
      projectName: selectedProject?.name ?? projectId,
      projectContext,
      contentType: selectedContentType?.label ?? contentType,
      outputLanguage,
      purpose,
      audience,
      tone,
      outputFormat,
      qualityLevel,
      title: title.trim(),
      brief: brief.trim()
    });

    const basePayload = {
      project_id: projectId,
      content_type: contentType,
      title: title.trim() || undefined,
      brief: enhancedBrief,
      prompt: enhancedBrief,
      model: model || undefined,
      provider: "ollama",
      save_output: saveOutput
    };

    try {
      const contentEndpoint = `${apiBaseUrl}/content/generate`;
      const contentResponse = await postJson(contentEndpoint, basePayload);

      if (contentResponse.ok) {
        setResult({
          ok: true,
          endpoint: contentEndpoint,
          raw: contentResponse.data,
          outputText: extractOutput(contentResponse.data),
          assetId: extractAssetId(contentResponse.data)
        });
        return;
      }

      const workflowEndpoint = `${apiBaseUrl}/workflows/projects/${projectId}/generate`;
      const workflowResponse = await postJson(workflowEndpoint, {
        content_type: contentType,
        title: title.trim() || undefined,
        brief: enhancedBrief,
        prompt: enhancedBrief,
        model: model || undefined,
        provider: "ollama",
        save_output: saveOutput
      });

      if (workflowResponse.ok) {
        setResult({
          ok: true,
          endpoint: workflowEndpoint,
          raw: workflowResponse.data,
          outputText: extractOutput(workflowResponse.data),
          assetId: extractAssetId(workflowResponse.data)
        });
        return;
      }

      setResult({
        ok: false,
        endpoint: workflowEndpoint,
        raw: workflowResponse.data,
        outputText: extractOutput(workflowResponse.data),
        message: `endpoint اصلی خطا داد: HTTP ${contentResponse.status}. endpoint جایگزین هم خطا داد: HTTP ${workflowResponse.status}.`
      });
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "تولید محتوا ناموفق بود.");
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <div className="generation-grid">
      <form className="panel generation-form" onSubmit={handleSubmit}>
        <div className="panel-heading">
          <p className="eyebrow">فرم ساده تولید</p>
          <h2>چه چیزی می‌خواهی بسازی؟</h2>
        </div>

        <label>
          پروژه
          <select
            value={projectId}
            onChange={(event) => handleProjectChange(event.target.value)}
          >
            {projects.length > 0 ? (
              projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))
            ) : (
              <option value="">پروژه‌ای پیدا نشد</option>
            )}
          </select>
        </label>

        <label>
          نوع محتوا
          <select
            value={contentType}
            onChange={(event) => setContentType(event.target.value)}
          >
            {contentTypes.length > 0 ? (
              contentTypes.map((type) => (
                <option key={type.key} value={type.key}>
                  {type.label}
                </option>
              ))
            ) : (
              <option value="">نوع محتوا پیدا نشد</option>
            )}
          </select>
        </label>

        <label>
          مدل
          <select value={model} onChange={(event) => setModel(event.target.value)}>
            {models.length > 0 ? (
              models.map((modelOption) => (
                <option key={modelOption.name} value={modelOption.name}>
                  {modelOption.name}
                </option>
              ))
            ) : (
              <option value="">مدل پیش‌فرض بک‌اند</option>
            )}
          </select>
        </label>

        <label>
          زبان خروجی
          <select
            value={outputLanguage}
            onChange={(event) => setOutputLanguage(event.target.value)}
          >
            <option value="فارسی">فارسی</option>
            <option value="English">English</option>
            <option value="العربية">العربية</option>
            <option value="اردو">اردو</option>
          </select>
        </label>

        <label>
          هدف محتوا
          <input
            value={purpose}
            onChange={(event) => setPurpose(event.target.value)}
            placeholder="مثلاً معرفی، فروش، پیچ سرمایه‌گذاری، متن سایت"
          />
        </label>

        <label>
          مخاطب
          <input
            value={audience}
            onChange={(event) => setAudience(event.target.value)}
            placeholder="مثلاً سرمایه‌گذار، مشتری، کودک و نوجوان، مدیر سایت"
          />
        </label>

        <label>
          لحن
          <input
            value={tone}
            onChange={(event) => setTone(event.target.value)}
            placeholder="مثلاً حرفه‌ای، صمیمی، سینمایی، ساده، تجاری"
          />
        </label>

        <label>
          قالب خروجی
          <input
            value={outputFormat}
            onChange={(event) => setOutputFormat(event.target.value)}
            placeholder="مثلاً متن کوتاه، مقاله، تیتر و پاراگراف، جدول"
          />
        </label>

        <label>
          سطح کیفیت
          <select
            value={qualityLevel}
            onChange={(event) => setQualityLevel(event.target.value)}
          >
            <option value="کیفیت بالا، آماده استفاده، خاص پروژه، بدون کلی‌گویی">
              کیفیت بالا و آماده استفاده
            </option>
            <option value="خلاصه، دقیق، سریع و قابل کپی">
              خلاصه و سریع
            </option>
            <option value="حرفه‌ای، پرجزئیات، مناسب ارائه رسمی">
              رسمی و پرجزئیات
            </option>
            <option value="خلاقانه، تصویری، مناسب پروژه هنری و داستانی">
              خلاقانه و داستانی
            </option>
            <option value="تجاری، قانع‌کننده، مناسب فروش و بازاریابی">
              تجاری و بازاریابی
            </option>
          </select>
        </label>

        <label>
          اطلاعات ضروری پروژه
          <textarea
            value={projectContext}
            onChange={(event) => setProjectContext(event.target.value)}
            rows={5}
            placeholder="اینجا اطلاعات مهم پروژه را بنویس تا خروجی عمومی و بی‌کیفیت نشود."
          />
        </label>

        <label>
          عنوان اختیاری
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="مثلاً معرفی پروژه گرگران"
          />
        </label>

        <label>
          توضیح کار
          <textarea
            value={brief}
            onChange={(event) => setBrief(event.target.value)}
            rows={8}
            placeholder="اینجا دقیق بنویس چه محتوایی می‌خواهی..."
          />
        </label>

        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={saveOutput}
            onChange={(event) => setSaveOutput(event.target.checked)}
          />
          <span>save_output  خروجی تولیدشده ذخیره شود</span>
        </label>

        {error ? <p className="form-error">{error}</p> : null}

        <button type="submit" disabled={!canSubmit}>
          {isGenerating ? "در حال تولید..." : "تولید محتوا"}
        </button>
      </form>

      <section className="panel generation-output">
        <div className="panel-heading">
          <p className="eyebrow">خروجی</p>
          <h2>نتیجه تولید</h2>
        </div>

        {result ? (
          <>
            <div className="health-list">
              <div>
                <strong>وضعیت</strong>
                <span>{result.ok ? "تولید شد" : "خطا در تولید"}</span>
              </div>
              <div>
                <strong>مسیر استفاده‌شده</strong>
                <span>{result.endpoint}</span>
              </div>
              {result.message ? (
                <div>
                  <strong>پیام</strong>
                  <span>{result.message}</span>
                </div>
              ) : null}
              {result.assetId ? (
                <div>
                  <strong>محتوای ذخیره‌شده</strong>
                  <a href={`/content-assets/${result.assetId}`}>
                    باز کردن محتوا
                  </a>
                </div>
              ) : null}
            </div>

            <pre className="generated-output">{result.outputText}</pre>

            <details>
              <summary>پاسخ خام سیستم</summary>
              <pre className="json-block">{JSON.stringify(result.raw, null, 2)}</pre>
            </details>
          </>
        ) : (
          <div className="quality-help">
            <h3>برای خروجی بهتر</h3>
            <p>برای متن سایت، نوع محتوا را روی کپشن شبکه اجتماعی نگذار. بهتر است «مقاله»، «معرفی»، «Pitch» یا «General» را انتخاب کنی.</p>
            <ul>
              <li>در «اطلاعات ضروری پروژه»، زمینه داستان یا برند را بنویس.</li>
              <li>در «توضیح کار»، دقیق بگو خروجی کجا استفاده می‌شود.</li>
              <li>اگر متن سایت می‌خواهی، صریح بنویس «کپشن شبکه اجتماعی نباشد».</li>
              <li>اگر ایموجی نمی‌خواهی، همان‌جا هم تأکید کن.</li>
            </ul>
          </div>
        )}
      </section>
    </div>
  );
}
'''.strip() + "\n",
encoding="utf-8"
)

print("GenerateContentForm improved for output extraction and quality prompting.")
