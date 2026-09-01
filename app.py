import io
import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

# -----------------------------------------------------------------------------
# 0. 기본 설정 및 세션 상태(Session State) 초기화
# -----------------------------------------------------------------------------
st.set_page_config(page_title="초등 장보기 미션 앱", page_icon="🛒", layout="wide")

MISSIONS = {
    "카레 만들기 🍛": 15000,
    "여름캠핑 준비하기 ⛺": 35000,
    "친구 생일파티 준비하기 🎂": 25000
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

# 결과 이미지 생성 함수 (다운로드용)
def generate_result_image(mission, budget, cart, total_spent, balance, reason):
    width, height = 600, 750
    img = Image.new('RGB', (width, height), color='#FFFFFF')
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("malgun.ttf", 22)
        font_sub = ImageFont.truetype("malgun.ttf", 14)
        font_body = ImageFont.truetype("malgun.ttf", 15)
        font_bold = ImageFont.truetype("malgunbd.ttf", 16)
    except:
        font_title = font_sub = font_body = font_bold = ImageFont.load_default()

    draw.rectangle([(10, 10), (width-10, height-10)], outline='#E0E0E0', width=3)
    draw.rectangle([(20, 20), (width-20, 80)], fill='#FFECEC')
    draw.text((width//2, 35), f"미션: {mission}", fill='#FF4B4B', font=font_title, anchor="mm")
    draw.text((width//2, 63), "초등 장보기 미션 결과표", fill='#777777', font=font_sub, anchor="mm")
    
    draw.text((30, 100), "🛒 구매한 물건 목록", fill='#2C3E50', font=font_bold)
    y_offset = 130
    for name, item in cart.items():
        item_total = item['price'] * item['qty']
        text_line = f"• {name} ({item['price']:,}원 × {item['qty']}개)"
        draw.text((40, y_offset), text_line, fill='#333333', font=font_body)
        draw.text((width-40, y_offset), f"{item_total:,}원", fill='#2C3E50', font=font_bold, anchor="ra")
        y_offset += 28
        if y_offset > 380:
            break
            
    draw.rectangle([(30, 420), (width-30, 550)], fill='#F8F9FA', outline='#DDDDDD')
    draw.text((50, 440), "총 예산:", fill='#333333', font=font_body)
    draw.text((width-50, 440), f"{budget:,}원", fill='#333333', font=font_bold, anchor="ra")
    
    draw.text((50, 475), "사용한 금액:", fill='#333333', font=font_body)
    draw.text((width-50, 475), f"{total_spent:,}원", fill='#E74C3C', font=font_bold, anchor="ra")
    
    draw.line([(50, 510), (width-50, 510)], fill='#CCCCCC', width=1)
    draw.text((50, 520), "남은 돈 (차액):", fill='#333333', font=font_body)
    draw.text((width-50, 520), f"{balance:,}원", fill='#27AE60', font=font_bold, anchor="ra")
    
    draw.rectangle([(30, 570), (width-30, 710)], fill='#FFF9DB', outline='#F1C40F')
    draw.text((45, 580), "💬 내가 작성한 구매 이유", fill='#D35400', font=font_bold)
    
    lines = []
    words = reason.split(' ')
    curr_line = ""
    for w in words:
        if len(curr_line + w) > 35:
            lines.append(curr_line)
            curr_line = w + " "
        else:
            curr_line += w + " "
    lines.append(curr_line)
    
    ry = 610
    for line in lines[:4]:
        draw.text((45, ry), line.strip(), fill='#444444', font=font_body)
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
        st.session_state.page = 'shopping'
        st.rerun()

# -----------------------------------------------------------------------------
# 2. 쇼핑 화면
# -----------------------------------------------------------------------------
elif st.session_state.page == 'shopping':
    st.title(f"🛍️ 쇼핑하기 - {st.session_state.selected_mission}")
    st.caption(f"주어진 예산: **{st.session_state.budget:,}원**")
    st.divider()

    cols = st.columns(3)
    for idx, row in df_products.iterrows():
        name = row['품명']
        price = int(row['가격'])
        img_url = row['이미지 url']
        
        with cols[idx % 3]:
            with st.container(border=True):
                st.image(img_url, use_container_width=True)
                st.subheader(name)
                st.write(f"**가격:** {price:,}원")
                
                curr_qty = st.number_input(f"수량 ({name})", min_value=0, max_value=20, value=0, key=f"qty_{idx}", label_visibility="collapsed")
                
                if st.button(f"장바구니 담기", key=f"add_{idx}"):
                    if curr_qty > 0:
                        st.session_state.cart[name] = {"price": price, "qty": curr_qty, "image": img_url}
                        st.toast(f"'{name}' {curr_qty}개가 장바구니에 담겼습니다! 🛒")
                    else:
                        if name in st.session_state.cart:
                            del st.session_state.cart[name]
                            st.toast(f"'{name}'이(가) 장바구니에서 삭제되었습니다.")

    st.divider()
    st.header("🧺 내가 담은 장바구니")
    
    total_price = 0
    if not st.session_state.cart:
        st.write("아직 장바구니에 담은 물건이 없습니다.")
    else:
        cart_data = []
        for name, item in st.session_state.cart.items():
            subtotal = item['price'] * item['qty']
            total_price += subtotal
            cart_data.append({
                "품명": name,
                "단가": f"{item['price']:,}원",
                "수량": item['qty'],
                "합계": f"{subtotal:,}원"
            })
        st.dataframe(pd.DataFrame(cart_data), use_container_width=True)

    rem_budget = st.session_state.budget - total_price
    
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
# 3. 결과 화면 (Streamlit 전용 UI 요소 활용)
# -----------------------------------------------------------------------------
elif st.session_state.page == 'result':
    st.title("🎉 장보기 미션 완료!")
    st.caption("선택한 물건과 구매 이유를 확인하고 이미지로 다운로드 받으세요.")
    
    total_spent = sum(item['price'] * item['qty'] for item in st.session_state.cart.values())
    balance = st.session_state.budget - total_spent

    st.subheader("💡 구매 이유 작성하기")
    reason_input = st.text_area(
        "이 물건들을 선택한 이유를 작성해 주세요!",
        value=st.session_state.purchase_reason,
        placeholder="이유를 입력해 주세요...",
        height=100
    )
    st.session_state.purchase_reason = reason_input
    st.divider()

    # 순수 Streamlit UI로 구성된 결과 리포트 카드 (코드 노출 무조건 방지)
    with st.container(border=True):
        st.markdown(f"### 🎯 미션: {st.session_state.selected_mission}")
        st.divider()
        
        st.markdown("#### 🛒 구매한 물건 목록")
        for name, item in st.session_state.cart.items():
            col1, col2, col3 = st.columns([1, 3, 2])
            with col1:
                st.image(item['image'], width=50)
            with col2:
                st.write(f"**{name}**")
                st.caption(f"{item['price']:,}원 × {item['qty']}개")
            with col3:
                st.write(f"**{item['price']*item['qty']:,}원**")
        
        st.divider()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("총 예산", f"{st.session_state.budget:,}원")
        c2.metric("사용한 금액", f"{total_spent:,}원")
        c3.metric("남은 돈 (차액)", f"{balance:,}원")
        
        st.divider()
        
        st.markdown("#### 💬 내가 작성한 구매 이유")
        if reason_input.strip():
            st.info(reason_input)
        else:
            st.warning("작성된 이유가 없습니다.")

    st.write("")

    if reason_input.strip():
        st.subheader("🖼️ 그림으로 저장하기")
        
        img_bytes = generate_result_image(
            st.session_state.selected_mission,
            st.session_state.budget,
            st.session_state.cart,
            total_spent,
            balance,
            reason_input
        )
        
        st.download_button(
            label="📸 그림으로 저장하기",
            data=img_bytes,
            file_name="장보기_미션_결과.png",
            mime="image/png",
            type="primary"
        )
    else:
        st.warning("⚠️ '구매 이유'를 작성하면 [그림으로 저장] 버튼이 나타납니다.")

    st.write("")
    if st.button("🔄 다시 시작하기"):
        st.session_state.page = 'start'
        st.rerun()
