# 상품 진열장 (3열 레이아웃)
    cols = st.columns(3)
    for idx, row in df_products.iterrows():
        name = row['품명']
        price = int(row['가격'])
        img_url = row['이미지 url']
        
        with cols[idx % 3]:
            with st.container(border=True):
                # use_column_width -> use_container_width 로 변경
                st.image(img_url, use_container_width=True)
                st.subheader(name)
                st.write(f"**가격:** {price:,}원")
