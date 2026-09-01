import streamlit as st
import pandas as pd
import html

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
                # use_container_width=True 로 최신버전 호환성 수정 완료
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
# 3. 결과 화면
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

    cart_items_html = ""
    for name, item in st.session_state.cart.items():
        item_total = item['price'] * item['qty']
        cart_items_html += f"""
        <div style="display: flex; align-items: center; border-bottom: 1px solid #eee; padding: 8px 0;">
            <img src="{item['image']}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px; margin-right: 15px;" />
            <div style="flex-grow: 1;">
                <strong style="font-size: 16px; color: #333;">{html.escape(name)}</strong><br/>
                <span style="font-size: 14px; color: #666;">{item['price']:,}원 × {item['qty']}개</span>
            </div>
            <div style="font-size: 16px; font-weight: bold; color: #2c3e50;">
                {item_total:,}원
            </div>
        </div>
        """

    safe_reason = html.escape(reason_input) if reason_input else "작성된 이유가 없습니다."

    result_card_html = f"""
    <div id="capture-card" style="
        width: 550px; 
        padding: 25px; 
        background: #ffffff; 
        border-radius: 12px; 
        border: 2px solid #e0e0e0;
        font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: #333;
    ">
        <div style="text-align: center; border-bottom: 2px solid #FF4B4B; padding-bottom: 12px; margin-bottom: 15px;">
            <h2 style="margin: 0; color: #FF4B4B; font-size: 22px;">미션: {st.session_state.selected_mission}</h2>
            <p style="margin: 5px 0 0 0; color: #888; font-size: 13px;">초등 장보기 미션 결과표</p>
        </div>

        <div style="margin-bottom: 15px;">
            <h4 style="margin: 0 0 10px 0; color: #2c3e50;">🛒 구매한 물건 목록</h4>
            {cart_items_html}
        </div>

        <div style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 14px;">
                <span>총 예산:</span> <strong>{st.session_state.budget:,}원</strong>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 14px;">
                <span>사용한 금액:</span> <strong style="color: #e74c3c;">{total_spent:,}원</strong>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 15px; border-top: 1px solid #ddd; padding-top: 5px;">
                <span>남은 돈(차액):</span> <strong style="color: #27ae60;">{balance:,}원</strong>
            </div>
        </div>

        <div style="background: #fff9db; padding: 12px; border-radius: 8px; border-left: 4px solid #f1c40f;">
            <h4 style="margin: 0 0 5px 0; color: #d35400; font-size: 14px;">💬 내가 작성한 구매 이유</h4>
            <p style="margin: 0; font-size: 13px; color: #444; white-space: pre-wrap; word-break: break-all;">{safe_reason}</p>
        </div>
    </div>
    """

    st.markdown(result_card_html, unsafe_allow_html=True)
    st.write("")

    if reason_input.strip():
        st.subheader("🖼️ 그림으로 저장하기")
        st.caption("아래 '그림으로 저장하기' 버튼을 누르면 인쇄용 이미지 파일이 다운로드됩니다.")
        
        download_js = """
        <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
        <button onclick="downloadImage()" style="
            background-color: #FF4B4B;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            font-weight: bold;
        ">📸 그림으로 저장하기</button>
        <script>
        function downloadImage() {
            var card = window.parent.document.getElementById('capture-card');
            if(!card) card = document.getElementById('capture-card');
            
            html2canvas(card, {useCORS: true, scale: 2}).then(function(canvas) {
                var link = document.createElement('a');
                link.download = '장보기_미션_결과.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
            });
        }
        </script>
        """
        st.components.v1.html(download_js, height=60)
    else:
        st.warning("⚠️ '구매 이유'를 작성하면 [그림으로 저장] 버튼이 생성됩니다.")

    st.write("")
    if st.button("🔄 다시 시작하기"):
        st.session_state.page = 'start'
        st.rerun()
