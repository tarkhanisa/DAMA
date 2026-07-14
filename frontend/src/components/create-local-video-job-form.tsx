"use client";

import { FormEvent, useState } from "react";
import { friendlyErrorMessage } from "../lib/persian-copy";

type CreateLocalVideoJobFormProps = {
  apiBaseUrl: string;
};

export function CreateLocalVideoJobForm({ apiBaseUrl }: CreateLocalVideoJobFormProps) {
  const [projectName, setProjectName] = useState("");
  const [title, setTitle] = useState("");
  const [startImage, setStartImage] = useState("");
  const [endImage, setEndImage] = useState("");
  const [prompt, setPrompt] = useState("");
  const [negativePrompt, setNegativePrompt] = useState("");
  const [duration, setDuration] = useState("4");
  const [aspectRatio, setAspectRatio] = useState("16:9");
  const [fps, setFps] = useState("24");
  const [message, setMessage] = useState("");
  const [jobLink, setJobLink] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isEnhancing, setIsEnhancing] = useState(false);

  async function handleEnhancePrompt() {
    setIsEnhancing(true);
    setMessage("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/local-video/prompt/enhance`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          project_name: projectName,
          title,
          start_image: startImage,
          end_image: endImage,
          prompt,
          negative_prompt: negativePrompt,
          duration_seconds: Number(duration),
          aspect_ratio: aspectRatio,
          fps: Number(fps)
        })
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(friendlyErrorMessage(String(payload.detail ?? `HTTP ${response.status}`)));
        return;
      }

      if (payload.enhanced_prompt) {
        setPrompt(String(payload.enhanced_prompt));
      }

      if (payload.negative_prompt) {
        setNegativePrompt(String(payload.negative_prompt));
      }

      setMessage(payload.message ?? "پرامپت بهبود داده شد.");
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
    } finally {
      setIsEnhancing(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSaving(true);
    setMessage("");
    setJobLink("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/local-video/jobs`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          project_name: projectName,
          title,
          start_image: startImage,
          end_image: endImage,
          prompt,
          negative_prompt: negativePrompt,
          duration_seconds: Number(duration),
          aspect_ratio: aspectRatio,
          fps: Number(fps)
        })
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(friendlyErrorMessage(String(payload.detail ?? `HTTP ${response.status}`)));
        return;
      }

      setMessage("درخواست ویدیو ساخته شد. حالا میتوانی dry-run بگیری یا موتور لوکال را اجرا کنی.");
      setJobLink(`/produce/video/${payload.id}`);
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="panel generation-form local-video-form" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <p className="eyebrow">ویدیو لوکال</p>
        <h2>ساخت درخواست ویدیو از تصویر</h2>
      </div>

      <label>
        پروژه
        <input
          value={projectName}
          onChange={(event) => setProjectName(event.target.value)}
          placeholder="مثلا درخت و دختر دامامدیا اورماشاپ..."
        />
      </label>

      <label>
        عنوان ویدیو
        <input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="مثلا حرکت آرام پوستر به نمای سینمایی"
        />
      </label>

      <label>
        تصویر شروع
        <input
          value={startImage}
          onChange={(event) => setStartImage(event.target.value)}
          placeholder="مسیر فایل یا لینک تصویر شروع مثل I:/DAMA/media/start.png"
          required
        />
      </label>

      <label>
        تصویر پایان اختیاری
        <input
          value={endImage}
          onChange={(event) => setEndImage(event.target.value)}
          placeholder="اگر لازم است مسیر تصویر پایان را وارد کن"
        />
      </label>

      <label>
        پرامپت حرکت
        <textarea
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          placeholder="مثلا: حرکت آرام دوربین زوم نرم نور سینمایی تبدیل تدریجی به تصویر پایان..."
          rows={6}
          required
        />
      </label>

      <div className="actions">
        <button
          type="button"
          onClick={handleEnhancePrompt}
          disabled={isEnhancing || !prompt}
        >
          {isEnhancing ? "در حال بهبود..." : "بهبود پرامپت با Ollama/Qwen"}
        </button>
      </div>

      <label>
        پرامپت منفی اختیاری
        <textarea
          value={negativePrompt}
          onChange={(event) => setNegativePrompt(event.target.value)}
          placeholder="مثلا: لرزش زیاد تغییر چهره اعوجاج نوشته اضافه فریم خراب"
          rows={3}
        />
      </label>

      <div className="form-grid-3">
        <label>
          مدت ویدیو
          <input
            type="number"
            min="1"
            max="30"
            step="0.5"
            value={duration}
            onChange={(event) => setDuration(event.target.value)}
          />
        </label>

        <label>
          نسبت تصویر
          <select value={aspectRatio} onChange={(event) => setAspectRatio(event.target.value)}>
            <option value="16:9">افقی 16:9</option>
            <option value="9:16">عمودی 9:16</option>
            <option value="1:1">مربع 1:1</option>
            <option value="4:5">پست 4:5</option>
            <option value="3:4">عمودی 3:4</option>
            <option value="4:3">قدیمی 4:3</option>
          </select>
        </label>

        <label>
          فریمریت
          <input
            type="number"
            min="8"
            max="60"
            value={fps}
            onChange={(event) => setFps(event.target.value)}
          />
        </label>
      </div>

      <p className="muted-note">
        Ollama/Qwen پرامپت را بهتر میکند. ساخت واقعی ویدیو با موتور لوکال انجام میشود که باید جداگانه وصل شود.
      </p>

      {message ? <p className="form-message">{message}</p> : null}

      {jobLink ? (
        <div className="actions">
          <a href={jobLink}>مشاهده درخواست ویدیو</a>
          <a href="/produce/video">درخواستهای ویدیو</a>
        </div>
      ) : null}

      <button type="submit" disabled={isSaving || !startImage || !prompt}>
        {isSaving ? "در حال ثبت..." : "ثبت درخواست ویدیو"}
      </button>
    </form>
  );
}
