import streamlit as st
import requests

API_URL = "http://localhost:8880"

st.title("Knowledge Management System")
st.sidebar.header("เมนู")

page = st.sidebar.selectbox("เลือกเมนู", ["เพิ่มความรู้", "ค้นหาความรู้", "อัปโหลดไฟล์ PDF"])

if page == "เพิ่มความรู้":
    st.header("เพิ่มความรู้ใหม่")

    title = st.text_input("หัวเรื่อง")
    description = st.text_area("รายละเอียด")

    if st.button("บันทึกความรู้"):
        response = requests.post(
            f"{API_URL}/add-documents", 
            data={"title": title, "description": description}
        )        
        if response.status_code == 200:
            st.success("เพิ่มความรู้เรียบร้อยแล้ว!")
        else:
            st.error("เกิดข้อผิดพลาดในการเพิ่มความรู้")

elif page == "ค้นหาความรู้":
    st.header("ค้นหาความรู้")

    query = st.text_input("กรอกคำค้นหา")
    top_k = st.slider("จำนวนผลลัพธ์ที่ต้องการ", 1, 10, 5)

    if st.button("ค้นหา"):
        response = requests.get(
            f"{API_URL}/similarity_search", 
            params={"query": query, "top_k": top_k}
        )
        
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                st.write("ผลการค้นหา:")
                for result in results:
                    st.subheader(result["title"])
                    st.write(result["content"])
                    st.write(f"คะแนน: {result['score']}")
                    st.write("---")
            else:
                st.warning("ไม่พบผลลัพธ์")
        else:
            st.error("เกิดข้อผิดพลาดในการค้นหา")

elif page == "อัปโหลดไฟล์ PDF":
    st.header("อัปโหลดไฟล์ PDF")

    uploaded_file = st.file_uploader("เลือกไฟล์ PDF", type=["pdf"])

    if st.button("อัปโหลด") and uploaded_file is not None:
        files = {"file": uploaded_file.getvalue()}
        response = requests.post(f"{API_URL}/ocr", files=files)
        
        if response.status_code == 200:
            results = response.json().get("results", [])
            st.write("สรุปเนื้อหาจากไฟล์ PDF:")
            st.write(results)
        else:
            st.error("เกิดข้อผิดพลาดในการอัปโหลดไฟล์ PDF")