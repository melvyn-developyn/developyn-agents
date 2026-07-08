# VitaSpan — patient-facing wording for legal review

Hi team,

We're building three patient-facing features that need short pieces of legal wording. We've drafted proposals below so development isn't blocked — each string lives in a single config constant, so you can change the wording at any point without engineering rework. Could you review and return final wording (or approve as-is)?

For context, VitaSpan stores patient medical records; the wording appears in the patient web app.

---

## 1. AI-generated content disclaimer

**Where it appears:** next to every AI-generated output (document summaries, categorisation, chat answers).

**Draft:**

> "AI-generated information may be incomplete or inaccurate. It does not replace medical advice and should be reviewed by an appropriately qualified healthcare professional before being relied upon."

**What we need from you:** confirm this adequately limits liability for AI output in a medical-records context, and whether any regulator-specific phrasing (e.g. MHRA/medical-device positioning) is required.

## 2. Account closure / deletion — retention notice

**Where it appears:** when a patient requests account closure or data deletion, before they confirm.

**Draft:**

> "Requesting closure or deletion starts a review by our team. We'll disable access to your account, but we may be legally and professionally required to retain some health records for a set period before they can be deleted. We'll confirm what has been actioned once your request has been reviewed."

**What we need from you:** confirm the retention framing is correct for health records (UK GDPR right-to-erasure carve-outs, NHS records-retention obligations if applicable), and whether we must state a specific retention period.

## 3. Consent withdrawal — consequences notice

**Where it appears:** when a patient withdraws a previously given consent (e.g. data processing for a feature), before they confirm.

**Draft:**

> "Withdrawing this consent may disable some platform features and stop us processing your health data for them. It does not automatically delete records we're required to keep. Your request will be reviewed and we'll confirm the outcome."

**What we need from you:** confirm this correctly separates consent withdrawal from erasure, and that a review-based (not instant) withdrawal process is acceptable.

---

**Also outstanding (separate workstream):** the Patient Terms & Privacy Notice document is still in internal draft review. Once finalised, we need the published URLs and a version identifier — signup acceptance is built against these.

Timeline: we'd like final wording within the current sprint if possible; drafts are already in the build marked "pending legal sign-off".

Thanks,
Melvyn
