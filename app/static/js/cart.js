function addToCart(id,image,name,unit_price){
    //axios fetch
    const quantity = document.getElementById('quantity').value;  // Lấy số lượng từ input

    fetch('/api/cart',{
        method: "post",
        body: JSON.stringify({
            "id": id,
            "image": image,
            "name": name,
            "unit_price": unit_price,
            "quantity": quantity
        }),
        headers: {
            "Content-Type": "application/json"
        }
    }).then(res => res.json()).then(data => {
       console.info('API Response:', data); // Kiểm tra phản hồi tại đây
       if (data.message) {
          toastr.success(data.message);  // Hiển thị thông báo thành công
       } else {
          console.error('Không có thông báo trong phản hồi từ API!');
       }
       console.info(data.total_quantity)
        // Kiểm tra total_quantity trước khi cập nhật giao diện

            let counters = document.getElementsByClassName("cart-counter");
            for (let i = 0; i < counters.length; i++) {
                counters[i].innerText = data.cart_stats.total_quantity;
            }

    }) //json promise
}

function updateCart(book_id,obj){
    fetch(`/api/cart/${book_id}`, {
        method: "put",
        body: JSON.stringify({
           "quantity":obj.value
        }),
        headers: {
            "Content-Type": "application/json"
        }
    }).then(res => res.json()).then(data => {
        console.info(data)
        let d = document.getElementsByClassName("cart-counter")
        for (let i = 0; i<d.length;i++)
            d[i].innerText = data.total_quantity

        let d2 = document.getElementsByClassName("cart-amount")
        for (let i = 0; i < d2.length; i++)
            d2[i].innerText = data.total_amount.toLocaleString("en-US")
    }) //json promise
}

function deleteCart(book_id){
    if (confirm("Bạn chắc chắn xóa không?") == true){
        fetch(`/api/cart/${book_id}`, {
            method: "delete"
        }).then(res => res.json()).then(data => {
            console.info(data)
            if (data.message) {
              toastr.success(data.message);  // Hiển thị thông báo thành công
            } else {
              console.error('Không có thông báo trong phản hồi từ API!');
            }
            let d = document.getElementsByClassName("cart-counter")
            for (let i = 0; i<d.length;i++)
                d[i].innerText = data.cart_stats.total_quantity

            let d2 = document.getElementsByClassName("cart-amount")
            for (let i = 0; i < d2.length; i++)
                d2[i].innerText = data.cart_stats.total_amount.toLocaleString("en-US")

            let c = document.getElementById(`cart${book_id}`)
            c.style.display = "none"
        }).catch(err => console.info(err)) //json promise
    }
}


function buyNow(id, image, name, unit_price) {
    const quantity = document.getElementById('quantity').value; // Lấy số lượng từ input
    fetch('/api/cart', {
        method: "post",
        body: JSON.stringify({
            "id": id,
            "image": image,
            "name": name,
            "unit_price": unit_price,
            "quantity": quantity
        }),
        headers: {
            "Content-Type": "application/json"
        }
    })
    .then(res => res.json())
    .then(data => {
        console.info(data);
        if (data.message) {
            window.location.href = '/cart';
        } else {
            console.error('Không có thông báo trong phản hồi từ API!');
        }
    })
    .catch(error => {
        console.error("Lỗi khi mua ngay:", error);
    });
}

function pay() {
    if (confirm("Bạn chắc chắn thanh toán?") === true) {
        // Dữ liệu giả định gửi lên server
        const data = {
            order_id: "123456",         // Mã đơn hàng
            amount: 100000,            // Số tiền (VNĐ)
            order_desc: "Thanh toán đơn hàng",  // Mô tả đơn hàng
            bank_code: ""              // Mã ngân hàng (nếu cần)
        };

        fetch('/api/pay', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 200) {
                // Điều hướng tới URL thanh toán
                window.location.href = data.payment_url;
            } else {
                alert("Có lỗi xảy ra: " + (data.message || "Không rõ nguyên nhân"));
            }
        })
        .catch(err => {
            console.error(err);
            alert("Không thể kết nối tới server. Vui lòng thử lại sau!");
        });
    }
}