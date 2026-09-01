import io
import os
import requests
import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

# -----------------------------------------------------------------------------
# 0. 기본 설정 및 세션 상태(Session State) 초기화
# -----------------------------------------------------------------------------
st.set_page_config(page_title="초등 장보기 미션 앱", page_icon="🛒", layout="wide")

# 1. 미션 및 어울리는 이모지 설정
MISSIONS = {
    "🍛 카레 만들기": 15000,
    "⛺ 여름캠핑 준비하기": 35000,
    "🎉 친구 생일파티 준비하기": 25000
}

if 'page' not in st.session_state:
    st.session_state.page = 'start'
if 'selected_mission' not in st.session_state:
    st.session_state.selected_mission = None
if 'budget' not in st.session_state:
    st.session_state.budget = 0
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'purchase_reason' not in st.session_state:
    st.session_state.purchase_reason = ""
if 'reason_submitted' not in st.session_state:
    st.session_state.reason_submitted = False

@st.cache_data
def load_products():
    try:
        df = pd.read_csv('products.csv')
        return df
    except Exception:
        return pd.DataFrame({
            '품명': ['당근', '감자', '양파', '카레용 고기', '카레가루', '텐트', '음료수', '생일케이크'],
            '가격': [1000, 1500, 1200, 6000, 2500, 20000, 1500, 15000],
            '이미지 url': ['https://via.placeholder.com/150'] * 8
        })

df_products = load_products()

# -----------------------------------------------------------------------------
# 한글 폰트 자동 다운로드 함수 (PNG 생성 시 깨짐 방지)
# -----------------------------------------------------------------------------
@st.cache_resource
def get_korean_font(size):
    font_filename = "NanumGothic.ttf"
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    
    if not os.path.exists(font_filename):
        try:
            res = requests.get(font_url, timeout=5)
            with open(font_filename, "wb") as f:
                f.write(res.content)
        except Exception:
            pass
            
    try:
        return ImageFont.truetype(font_filename, size)
    except Exception:
        return ImageFont.load_default()

# -----------------------------------------------------------------------------
# 결과 이미지 생성 함수 (Pillow)
# -----------------------------------------------------------------------------
def generate_result_image(mission, budget, cart, total_spent, balance, reason):
    width, height = 650, 800
    img = Image.new('RGB', (width, height), color='#FFFFFF')
    draw = ImageDraw.Draw(img)
    
    font_title = get_korean_font(22)
    font_sub = get_korean_font(13)
    font_body = get_korean_font(14)
    font_bold = get_korean_font(15)

    # 외곽 테두리 및 헤더
    draw.rectangle([(10, 10), (width-10, height-10)], outline='#E0E0E0', width=3)
    draw.rectangle([(20, 20), (width-20, 85)], fill='#F0F4F8')
    draw.text((width//2, 40), f"미션: {mission}", fill='#1E3A8A', font=font_title, anchor="mm")
    draw.text((width//2, 68), "초등 장보기 미션 결과표", fill='#6B7280', font=font_sub, anchor="mm")
    
    # 구매품목 목록 Header
    draw.text((30, 105), "🛒 구매한 물건 목록", fill='#1F2937', font=font_bold)
    draw.line([(30, 128), (width-30, 128)], fill='#E5E7EB', width=1)
    
    y_offset = 140
    for name, item in cart.items():
        item_total = item['price'] * item['qty']
        text_line = f"• {name}  |  {item['price']:,}원 × {item['qty']}개"
        draw.text((40, y_offset), text_line, fill='#374151', font=font_body)
        draw.text((width-40, y_offset), f"{item_total:,}원", fill='#1F2937', font=font_bold, anchor="ra")
        y_offset += 28
        if y_offset > 420:
            break
            
    # 금액 정산 영역
    draw.rectangle([(30, 460), (width-30, 590)], fill='#F9FAFB', outline='#E5E7EB')
    draw.text((50, 480), "주어진 금액 (예산):", fill='#374151', font=font_body)
    draw.text((width-50, 480), f"{budget:,}원", fill='#374151', font=font_bold, anchor="ra")
    
    draw.text((50, 515), "총 사용 금액:", fill='#374151', font=font_body)
    draw.text((width-50, 515), f"{total_spent:,}원", fill='#DC2626', font=font_bold, anchor="ra")
    
    draw.line([(50, 550), (width-50, 550)], fill='#D1D5DB', width=1)
    draw.text((50, 560), "남은 돈 (잔액):", fill='#374151', font=font_body)
    draw.text((width-50, 560), f"{balance:,}원", fill='#16A34A', font=font_bold, anchor="ra")
    
    # 구매 이유 영역
    draw.rectangle([(30, 610), (width-30, 760)], fill='#FEF3C7', outline='#F59E0B')
    draw.text((45, 625), "💬 내가 작성한 구매 이유", fill='#B45309', font=font_bold)
    
    lines = []
    words = reason.split(' ')
    curr_line = ""
    for w in words:
        if len(curr_line + w) > 32:
            lines.append(curr_line)
            curr_line = w + " "
        else:
            curr_line += w + " "
    lines.append(curr_line)
    
    ry = 655
    for line in lines[:4]:
        draw.text((45, ry), line.strip(), fill='#4B5563', font=font_body)
        ry += 22

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


# -----------------------------------------------------------------------------
# 1. 시작 화면
# -----------------------------------------------------------------------------
if st.session_state.page == 'start':
    st.title("🛒 초등 장보기 미션 앱")
    st.subheader("오늘의 미션을 선택하고 정해진 예산 안에서 장을 봐보세요!")
    st.divider()
    
    mission_choice = st.radio("도전할 미션을 선택하세요:", options=list(MISSIONS.keys()), index=0)
    selected_budget = MISSIONS[mission_choice]
    st.info(f"💡 **{mission_choice}** 의 주어진 예산은 **{selected_budget:,}원** 입니다.")
    
    if st.button("장보러 가기 🚀", type="primary", use_container_width=True):
        st.session_state.selected_mission = mission_choice
        st.session_state.budget = selected_budget
        st.session_state.cart = {}
        st.session_state.purchase_reason = ""
        st.session_state.reason_submitted = False
        st.session_state.page = 'shopping'
        st.rerun()

# -----------------------------------------------------------------------------
# 2. 쇼핑 화면
# -----------------------------------------------------------------------------
elif st.session_state.page == 'shopping':
    st.title(f"🛍️ 쇼핑하기 - {st.session_state.selected_mission}")
    st.caption(f"주어진 예산: **{st.session_state.budget:,}원**")
    st.divider()

    # 1열당 3개의 고정 카드 UI 스타일 적용
    cols = st.columns(3)
    for idx, row in df_products.iterrows():
        name = row['품명']
        price = int(row['가격'])
        img_url = row['이미지 url']
        
        with cols[idx % 3]:
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #E5E7EB;
                    border-radius: 12px;
                    padding: 12px;
                    background-color: #FFFFFF;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    height: 250px;
                    justify-content: space-between;
                    margin-bottom: 10px;
                ">
                    <img src="{img_url}" style="
                        width: 120px;
                        height: 120px;
                        object-fit: cover;
                        border-radius: 8px;
                    " loading="lazy" />
                    <div style="text-align: center; margin-top: 8px;">
                        <div style="font-weight: bold; font-size: 16px; color: #1F2937;">{name}</div>
                        <div style="color: #4B5563; font-size: 14px; margin-top: 2px;">{price:,}원</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            curr_qty = st.number_input(
                f"수량 ({name})", 
                min_value=0, 
                max_value=20, 
                value=st.session_state.cart.get(name, {}).get('qty', 0), 
                key=f"qty_{idx}", 
                label_visibility="collapsed"
            )
            
            if st.button(f"장바구니 업데이트", key=f"add_{idx}", use_container_width=True):
                if curr_qty > 0:
                    st.session_state.cart[name] = {"price": price, "qty": curr_qty, "image": img_url}
                    st.toast(f"'{name}' {curr_qty}개가 장바구니에 담겼습니다! 🛒")
                else:
                    if name in st.session_state.cart:
                        del st.session_state.cart[name]
                        st.toast(f"'{name}'이(가) 장바구니에서 삭제되었습니다.")

    st.divider()
    st.header("🧺 내가 담은 장바구니")
    
    total_price = sum(item['price'] * item['qty'] for item in st.session_state.cart.values())
    rem_budget = st.session_state.budget - total_price

    if not st.session_state.cart:
        st.write("아직 장바구니에 담은 물건이 없습니다.")
    else:
        cart_html = """
        <div style="border: 1px solid #E5E7EB; border-radius: 8px; padding: 10px; background-color: #FAFAFA; margin-bottom: 15px;">
        """
        for name, item in st.session_state.cart.items():
            subtotal = item['price'] * item['qty']
            cart_html += f"""
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #EEEEEE;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{item['image']}" style="width: 45px; height: 45px; object-fit: cover; border-radius: 6px;" />
                    <div>
                        <span style="font-weight: bold; font-size: 15px; color: #333;">{name}</span><br/>
                        <span style="font-size: 13px; color: #666;">{item['price']:,}원 × {item['qty']}개</span>
                    </div>
                </div>
                <div style="font-weight: bold; font-size: 15px; color: #1E3A8A;">
                    {subtotal:,}원
                </div>
            </div>
            """
        cart_html += "</div>"
        st.markdown(cart_html, unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("총 예산", f"{st.session_state.budget:,}원")
    col_b.metric("현재 구매금액", f"{total_price:,}원")
    col_c.metric("남은 돈", f"{rem_budget:,}원", delta=rem_budget)

    is_over_budget = total_price > st.session_state.budget
    is_empty_cart = len(st.session_state.cart) == 0

    if is_over_budget:
        st.error(f"⚠️ 예산을 **{abs(rem_budget):,}원** 초과했습니다! 수량을 줄여주세요.")
    
    col_sub1, col_sub2 = st.columns([1, 1])
    with col_sub1:
        if st.button("← 처음으로", use_container_width=True):
            st.session_state.page = 'start'
            st.rerun()
            
    with col_sub2:
        submit_btn = st.button("제출하기 📝", type="primary", disabled=(is_over_budget or is_empty_cart), use_container_width=True)
        if submit_btn:
            st.session_state.page = 'result'
            st.rerun()

# -----------------------------------------------------------------------------
# 3. 결과 페이지
# -----------------------------------------------------------------------------
elif st.session_state.page == 'result':
    total_spent = sum(item['price'] * item['qty'] for item in st.session_state.cart.values())
    balance = st.session_state.budget - total_spent

    # 1. 상단 중앙 큰 글씨 미션 표기
    st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>미션: {st.session_state.selected_mission}</h1>", unsafe_allow_html=True)
    st.write("")
    
    # 2. 구매품목 목록 표시
    st.subheader("📦 구매품목")
    
    list_html = """
    <table style="width:100%; border-collapse: collapse; margin-bottom: 20px; font-size: 15px;">
        <thead>
            <tr style="border-bottom: 2px solid #333; text-align: left; background-color: #F3F4F6;">
                <th style="padding: 10px; width: 80px;">이미지</th>
                <th style="padding: 10px;">이름</th>
                <th style="padding: 10px; text-align: center;">수량</th>
                <th style="padding: 10px; text-align: right;">단가</th>
                <th style="padding: 10px; text-align: right;">합계</th>
            </tr>
        </thead>
        <tbody>
    """
    for name, item in st.session_state.cart.items():
        subtotal = item['price'] * item['qty']
        list_html += f"""
            <tr style="border-bottom: 1px solid #E5E7EB;">
                <td style="padding: 8px;"><img src="{item['image']}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 6px;"/></td>
                <td style="padding: 8px; font-weight: bold;">{name}</td>
                <td style="padding: 8px; text-align: center;">{item['qty']}개</td>
                <td style="padding: 8px; text-align: right;">{item['price']:,}원</td>
                <td style="padding: 8px; text-align: right; font-weight: bold;">{subtotal:,}원</td>
            </tr>
        """
    list_html += "</tbody></table>"
    st.markdown(list_html, unsafe_allow_html=True)

    # 3. 금액 요약
    st.subheader("💰 금액 정산")
    c1, c2, c3 = st.columns(3)
    c1.metric("주어진 금액 (예산)", f"{st.session_state.budget:,}원")
    c2.metric("총 사용 금액", f"{total_spent:,}원")
    c3.metric("남은 돈 (잔액)", f"{balance:,}원")
    
    st.divider()

    # 4. 구매이유 작성 및 제출 영역
    st.subheader("💬 구매 이유")
    reason_input = st.text_area(
        "선택한 물품들의 구매 이유를 작성해주세요:",
        value=st.session_state.purchase_reason,
        placeholder="예시: 카레를 만들기 위해 꼭 필요한 채소와 카레가루를 예산에 맞추어 구입했습니다.",
        height=100
    )
    
    if st.button("구매 이유 제출/적용 💾", type="primary"):
        if reason_input.strip():
            st.session_state.purchase_reason = reason_input
            st.session_state.reason_submitted = True
            st.success("구매 이유가 정상적으로 등록되었습니다!")
        else:
            st.warning("구매 이유를 입력해 주세요.")

    # 5. 구매 이유 제출 시 PNG로 다운로드 버튼 노출
    if st.session_state.reason_submitted and st.session_state.purchase_reason.strip():
        st.write("")
        st.success("👇 아래 버튼을 눌러 결과표를 PNG 이미지로 다운로드 받으세요!")
        
        img_bytes = generate_result_image(
            st.session_state.selected_mission,
            st.session_state.budget,
            st.session_state.cart,
            total_spent,
            balance,
            st.session_state.purchase_reason
        )
        
        st.download_button(
            label="📸 PNG로 다운받기",
            data=img_bytes,
            file_name="장보기_미션_결과.png",
            mime="image/png",
            type="primary",
            use_container_width=True
        )

    st.divider()
    if st.button("🔄 다시 시작하기"):
        st.session_state.page = 'start'
        st.rerun()
