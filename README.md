# 🛂 BioCheck – Smart Biosecurity Assistant

**Simplifying complex biosecurity checks into clearer guidance for everyday travellers.**

**BioCheck** is a web application designed to help travellers assess whether items they plan to bring into Australia may comply with biosecurity regulations.

Users can describe an item and upload an image of the product or barcode. The system then analyzes the available information and returns a simplified risk classification: **Allowed**, **Restricted**, or **Prohibited**.

This project was developed during **UNIHACK 2026**.

---

## 📑 Table of Contents

- [Overview](#overview)
- [Problem Statement](#-problem-statement)
- [Solution](#-solution)
- [Key Features](#️-key-features)
- [System Workflow](#️-system-workflow)
- [Tech Stack](#️-tech-stack)
- [Project Structure](#-project-structure)
- [Team Members](#-team-members)
- [Demo](#-demo)
- [Future Improvements](#-future-improvements)
- [Project Context](#project-context)
- [Disclaimer](#disclaimer)

---

## 🌏 Overview

Australia maintains strict biosecurity controls to protect its agriculture, environment, and public health. However, many travellers find it difficult to determine whether a food item, plant product, or animal-based product may be brought into the country.

BioCheck was created to make this process easier by providing a faster, more accessible way for users to check products before travelling.

---

## 🚨 Problem Statement

Travellers often face uncertainty when trying to interpret biosecurity requirements. Product labels may be unclear, ingredients may be unfamiliar, and official information can be difficult to process quickly in practical situations.

As a result, restricted items may be carried unintentionally, creating unnecessary stress and increasing the risk of confiscation or penalties at the border.

---

## 💡 Solution

BioCheck provides a simple pre-travel checking experience.

Users can:

- Enter a description of the item they want to bring
- Upload an image of the product or barcode
- Receive an AI-assisted risk assessment
- View a simplified classification result:
  - **Allowed**
  - **Restricted**
  - **Prohibited**

The goal is to help users make more informed decisions before arriving at the airport.

---

## ⚙️ Key Features

- **Mobile-friendly web interface**
- **Text-based product description input**
- **Image upload support** for product packaging or barcode
- **AI-assisted product and ingredient analysis**
- **Biosecurity rule comparison**
- **Classification output with simplified guidance**
- **User contribution support** for unknown or unlisted products

---

## 🏗️ System Workflow

1. The user enters a product description  
2. The user uploads an image of the product or barcode  
3. The AI analyzes the text and image input  
4. The system compares the result against the biosecurity rules database  
5. The user receives a classification and explanation  

---

## 🖥️ Tech Stack

### Frontend
- HTML
- CSS
- JavaScript

### Backend / Core Logic
- Python
- Flask

### AI / Data Components
- AI-based product classification
- Image analysis
- Biosecurity rule database

---

## 📁 Project Structure

```

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

- Automatic barcode recognition
- Expanded biosecurity rule coverage
- Improved AI accuracy for image and item analysis
- Broader product database support
- Integration with travel, airline, or airport-related services

---

## 📌 Project Context

BioCheck was developed as a hackathon prototype to explore how AI can improve accessibility and decision-making in travel-related biosecurity checking.

The project focuses on simplifying a complex process for everyday users and making technical information easier to understand.

---

## ⚠️ Disclaimer

BioCheck is intended as a **support tool** for preliminary checking only.  
It does **not** replace official Australian government biosecurity advice, declaration requirements, or border decisions.

Users should always refer to official sources when making final travel decisions.

---
