 🛂 Phobidden-Imports – Smart Biosecurity Assistant

**Simplifying complex biosecurity checks into clearer guidance for everyday travellers.**

**Phobidden-Imports** is a web application designed to help travellers assess whether items they plan to bring into Australia may comply with biosecurity regulations.

Users can describe an item and upload an image of the product or barcode. The system then analyzes the available information and returns a simplified risk classification: BRING IT, DECLARE IT, and DONT BRING.

This project was developed during **UNIHACK 2026**.

---

## 📑 Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Solution](#solution)
- [Key Features](#key-features)
- [System Workflow](#system-workflow)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Team Members](#team-members)
- [Future Improvements](#future-improvements)
- [Project Context](#project-context)
- [Disclaimer](#disclaimer)

---

## 🌏 Overview

Australia maintains strict biosecurity controls to protect its agriculture, environment, and public health. However, many travellers find it difficult to determine whether a food item, plant product, or animal-based product may be brought into the country.

Phobidden Imports was created to make this process easier by providing a faster, more accessible way for users to check products before travelling.

---

## 🚨 Problem Statement

Travellers often face uncertainty when trying to interpret biosecurity requirements. Product labels may be unclear, ingredients may be unfamiliar, and official information can be difficult to process quickly in practical situations.

As a result, restricted items may be carried unintentionally, creating unnecessary stress and increasing the risk of confiscation or penalties at the border.

---

## 💡 Solution

Phobidden Imports provides a simple pre-travel checking experience.

Users can:

- Enter a description of the item they want to bring
- Upload an image of the product or barcode
- Receive an AI-assisted risk assessment
- View a simplified classification result:
  - **Bring it**
  - **Declare it**
  - **Dont bring**

The goal is to help users make more informed decisions before arriving at the airport.

---

## ⚙️ Key Features

- **Multiple input options**  
  Users can check an item by typing a description, uploading a product photo, or scanning a barcode.

- **AI-powered extraction**  
  Gemini extracts key product details such as product name, ingredients, and packaging clues from text or images.

- **Barcode lookup support**  
  If a barcode is detected, the system can retrieve product information from Open Food Facts.

- **Category classification**  
  Products are classified into biosecurity-related categories such as dairy, meat, rice, sauces, tea, seafood, and more.

- **Rule-based evaluation**  
  The classified result is compared with rules in `reference.json` to determine the appropriate outcome.

- **Clear final verdict**  
  The system returns one of three simple results:
  - `BRING_IT`
  - `DECLARE_IT`
  - `DONT_BRING`

- **Explainable results**  
  The output also shows matched rules, reasons, and condition checks for better transparency.

---

## 🏗️ System Workflow

1. **User submits an item**  
   Input can be text, image, or barcode.

2. **Product information is extracted**  
   The system collects product details such as name, ingredients, and packaging status.

3. **Data is standardized**  
   All inputs are converted into one shared product format for processing.

4. **Product is classified**  
   Gemini identifies relevant categories and infers useful attributes.

5. **Rules are compared**  
   The system checks the classified result against the rules in `reference.json`.

6. **Final verdict is generated**  
   If multiple rules apply, the strictest result is chosen:
   `DONT_BRING` > `DECLARE_IT` > `BRING_IT`

---

## 🖥️ Tech Stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python, Flask
- **AI:** Google Gemini API
- **Barcode & Product Lookup:** pyzbar, Open Food Facts API
- **Image Processing:** Pillow (PIL)
- **Configuration:** python-dotenv
- **Rule Base:** JSON (`reference.json`)

---

## 📁 Project Structure

```
Phobidden-Imports/
├── function/
│   ├── classification.py
│   ├── compare.py
│   └── ingredient_extraction.py
├── static/
│   ├── about-use-style.css
│   ├── script.js
│   ├── styles.css
│   ├── user-reports-style.css
│   └── user-reports.js
├── templates/
│   ├── about-us.html
│   ├── biosecurity-checker.html
│   ├── index.html
│   └── user-reports.html
├── .env
├── .gitignore
├── app.py
├── README.md
└── reference.json
```
---

## 👥 Team members

| Name       | Role              | Contribution |
|------------|-------------------|--------------|
| Minh Triet | Team Leader       | Led project coordination, defined the product direction, and managed overall development progress |
| Khanh      | Design            | Designed the user interface and visual presentation of the application |
| Bi         | AI Classification | Developed the AI classification logic and product analysis workflow |
| Thao       | Database          | Built and structured the biosecurity rule database |
| Dat        | Database          | Supported database design, organization, and rule mapping |

---

## 🚀 Future Improvements

- Expanded biosecurity rule coverage
- Improved AI accuracy for image and item analysis
- Broader product database support
- Integration with travel, airline, or airport-related services

---

## 📌 Project Context

Phobidden-Imports was developed as a hackathon prototype to explore how AI can improve accessibility and decision-making in travel-related biosecurity checking.

The project focuses on simplifying a complex process for everyday users and making technical information easier to understand.

---

## ⚠️ Disclaimer

Phobidden-Imports is intended as a **support tool** for preliminary checking only.  
It does **not** replace official Australian government biosecurity advice, declaration requirements, or border decisions.

Users should always refer to official sources when making final travel decisions.