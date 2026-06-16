import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

def cao_text_tu_web(url):
    ket_qua = {
        "paragraphs": ["Failed to load page content."],
        "prev_url": "",
        "next_url": "",
        "chapters": [] 
    }
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            ket_qua["paragraphs"] = [f"Failed to load page. Error code: {response.status_code}"]
            return ket_qua
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. LẤY NỘI DUNG CHỮ TRUYỆN
        vung_chinh = (
            soup.find('div', class_='chapter-wrapper') or 
            soup.find('div', class_='chapter-c') or 
            soup.find('article') or 
            soup.find('div', class_='content') or 
            soup.find('div', id='content')
        )
        
        if vung_chinh:
            for br in vung_chinh.find_all("br"):
                br.replace_with("\n")
            raw_text = vung_chinh.get_text(separator="\n")
            lines = raw_text.split('\n')
            
            danh_sach_doan_van = []
            for line in lines:
                line_clean = line.strip()
                if line_clean and len(line_clean) > 1:
                    if "Chương " in line_clean and len(line_clean) < 50 and len(danh_sach_doan_van) > 3:
                        continue
                    danh_sach_doan_van.append(line_clean)
            if danh_sach_doan_van:
                ket_qua["paragraphs"] = danh_sach_doan_van
                
        tu_khoa_rac = ["post", "comment", "facebook", "report", "all_comment", "javascript", "#", "ủng hộ", "ung-ho", "login", "đăng nhập"]
        chu_dieu_huong_rac = ["chương trước", "chương sau", "prev", "next", "chap trước", "chap sau", "«", "»", "mục lục", "ủng hộ", "login", "đăng nhập"]

        # 2. TỰ ĐỘNG CÀO LINK CHƯƠNG TRƯỚC / CHƯƠNG SAU
        for a_tag in soup.find_all('a', href=True):
            text_nut = a_tag.get_text().lower()
            href_tuyet_doi = urljoin(url, a_tag['href'])
            
            if not any(rac in href_tuyet_doi.lower() for rac in tu_khoa_rac):
                if "chương trước" in text_nut or "prev" in text_nut or "chap trước" in text_nut:
                    ket_qua["prev_url"] = href_tuyet_doi
                if "chương sau" in text_nut or "next" in text_nut or "chap sau" in text_nut:
                    ket_qua["next_url"] = href_tuyet_doi

        # 3. THU THẬP TẤT CẢ LINK CHƯƠNG TRUYỆN THỰC TẾ
        danh_sach_tho = []
        
        select_tag = soup.find('select', class_=re.compile(r'chapter|select|nav')) or soup.find('select')
        if select_tag:
            for option in select_tag.find_all('option', value=True):
                ten_chuong = option.get_text().strip()
                link_chuong = urljoin(url, option['value'])
                if len(option['value']) > 2 and not any(rac in link_chuong.lower() for rac in tu_khoa_rac):
                    if not any(nav_rac in ten_chuong.lower() for nav_rac in chu_dieu_huong_rac):
                        num_check = re.search(r'chuong-(\d+)', link_chuong.lower())
                        if num_check:
                            danh_sach_tho.append({"title": ten_chuong, "url": link_chuong, "num": int(num_check.group(1))})
                        
        for a_tag in soup.find_all('a', href=True):
            text_link = a_tag.get_text().strip()
            href_tuyet_doi = urljoin(url, a_tag['href'])
            if ("chuong-" in href_tuyet_doi.lower() or "chapter-" in href_tuyet_doi.lower() or "Chương " in text_link) and len(text_link) < 60:
                if not any(rac in href_tuyet_doi.lower() for rac in tu_khoa_rac):
                    if not any(nav_rac in text_link.lower() for nav_rac in chu_dieu_huong_rac):
                        num_check = re.search(r'chuong-(\d+)', href_tuyet_doi.lower())
                        if num_check:
                            item_temp = {"title": text_link, "url": href_tuyet_doi, "num": int(num_check.group(1))}
                            if not any(d["url"] == href_tuyet_doi for d in danh_sach_tho):
                                danh_sach_tho.append(item_temp)

        danh_sach_tho.sort(key=lambda x: x["num"])
        ket_qua["chapters"] = [{"title": d["title"], "url": d["url"], "num": d["num"]} for d in danh_sach_tho]
        return ket_qua

    except Exception as e:
        ket_qua["paragraphs"] = [f"System error: {str(e)}"]
        return ket_qua