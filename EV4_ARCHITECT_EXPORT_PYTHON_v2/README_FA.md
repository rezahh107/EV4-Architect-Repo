# EV4 Architect Export — Python Wrapper v2

این نسخه خطای `ARCH_EXPORT_DIRTY_WORKTREE` مشاهده‌شده در v1 را هدف می‌گیرد.

## اصلاح اصلی

اجرای Python داخل checkout موقت اکنون با این policy انجام می‌شود:

```text
PYTHONDONTWRITEBYTECODE=1
PYTHONNOUSERSITE=1
```

بنابراین importهای exporter نمی‌توانند فایل‌های `__pycache__` یا `.pyc` داخل repository موقت ایجاد کنند.

همچنین وضعیت Git قبل و بعد از اجرای exporter ثبت می‌شود:

```text
pre-export-git-status.txt
post-export-git-status.txt
```

این نسخه به repository محلی `EV4-Project-Gate` نیاز ندارد. commit پذیرفته‌شده فعلی:

```text
be9bdea9ae246b1587043f2582c1a950ea2a6ec5
```

## اجرا

تمام فایل‌ها را کنار هم نگه دارید:

```text
Generate-ArchitectProjectGate.py
Run-ArchitectProjectGate.cmd
RPR-PG-001_architect_stage_payload.json
```

سپس اجرا کنید:

```text
Run-ArchitectProjectGate.cmd
```

ساختار پیشنهادی:

```text
E:\GitHub\EV4-Architect-Repo\EV4_ARCHITECT_EXPORT_PYTHON_v2\
```

## خروجی اصلی

```text
architect-project-gate.json
```

در صورت شکست، این فایل‌ها برای تشخیص دقیق نگه داشته می‌شوند:

```text
architect-project-gate.stderr.log
architect-project-gate.receipt.json
pre-export-git-status.txt
post-export-git-status.txt
driver.stdout.log
driver.stderr.log
```

## پیش‌نیازها

Windows:

```text
Python 3.10+
WSL
```

داخل WSL:

```text
git
python3
```
