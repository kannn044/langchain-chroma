import streamlit as st
import requests
import zipfile
import io

API_URL = "http://localhost:8880"
API_URL_OCR = "http://10.1.0.101:8890/"

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

    uploaded_files = st.file_uploader(
        "เลือกไฟล์ PDF หรือ ZIP", type=["pdf", "zip"], accept_multiple_files=True
    )

    if st.button("อัปโหลด") and uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.name.endswith(".zip"):
                # Process zip file
                with zipfile.ZipFile(io.BytesIO(uploaded_file.read())) as z:
                    for file_name in z.namelist():
                        if file_name.endswith(".pdf"):
                            with z.open(file_name) as pdf_file:
                                files = {"file": pdf_file.read()}
                                response = requests.post(f"{API_URL_OCR}/ocr", files=files)
                                if response.status_code == 200:
                                    results = response.json().get("results", [])
                                    st.write(f"ผลลัพธ์จากไฟล์: {file_name}")
                                    st.write(results)
                                else:
                                    st.error(f"เกิดข้อผิดพลาดในการประมวลผลไฟล์ {file_name}")
            elif uploaded_file.name.endswith(".pdf"):
                # Process single PDF file
                files = {"file": uploaded_file.getvalue()}
                response = requests.post(f"{API_URL_OCR}/ocr", files=files)
                if response.status_code == 200:
                    result = response.json()
                    
                    response_txt = requests.post(
                        f"{API_URL}/add-documents/txtfiles", 
                        data={
                            "title": f"ผลลัพธ์จากไฟล์: {uploaded_file.name}", "description": result["summary"], 
                            "filename": uploaded_file.name.replace(".pdf", ".txt"),
                        })

                    if response_txt.status_code == 200:
                        # Display the summary from OCR
                        st.write(f"ผลลัพธ์จากไฟล์: {uploaded_file.name}")
                        st.write(result["summary"])

                        # Generate download URL for the saved text file
                        download_filename = uploaded_file.name.replace(".pdf", ".txt")
                        download_url = f"{API_URL}/download-file/{download_filename}"

                        # Display download link
                        st.markdown(f"[ดาวน์โหลดไฟล์ข้อความต้นฉบับ]({API_URL}{download_url})")
                    else:
                        st.error("เกิดข้อผิดพลาดในการบันทึกไฟล์ข้อความ")
                else:
                    st.error("เกิดข้อผิดพลาดในการอัปโหลดไฟล์ PDF")
            else:
                st.error("เกิดข้อผิดพลาดในการประมวลผลไฟล์")