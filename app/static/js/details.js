//    Thêm vào danh sách yêu thích
    document.querySelector("#favourite-form").addEventListener("click", function (event) {
        event.preventDefault(); // Ngăn không reload trang

        const bookId = this.getAttribute("data-id"); // Lấy book_id từ nút

        fetch("/details?book_id=" + bookId, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
        })
        .then((response) => response.json())
        .then((data) => {
            if (data.error) {
                toastr.error(data.error); // Thông báo lỗi
            } else {
                toastr.success(data.message);; // Thông báo thành công
            }
        })
        .catch((error) => {
            console.error("Error:", error);
        });
    });
//  Gửi bình luận lên Server
    document.querySelector("#post-comment").addEventListener("click", function (event) {
    event.preventDefault();
    const urlParams = new URLSearchParams(window.location.search);
    const bookId = urlParams.get("book_id"); // Trích xuất giá trị của 'book_id'
    // Lấy dữ liệu từ DOM
    const comment = document.querySelector("#comment").value;
    const rating = document.querySelector("#rating").value;
    // Kiểm tra dữ liệu đầu vào
    if (!bookId || !comment || !rating) {
        toastr.error("Vui lòng điền đầy đủ thông tin!");
        return;
    }
    // Gửi request POST với fetch
    fetch("/post_comment", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            book_id: bookId,
            comment: comment,
            rating: rating,
        }),
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error("Lỗi từ máy chủ: " + response.statusText);
            }
            return response.json();
        })
        .then((data) => {
            if (data.error) {
                toastr.error(data.error); // Thông báo lỗi từ server
            } else {
                toastr.success(data.message); // Thông báo thành công
                fetchComments();
            }
        })
        .catch((error) => {
            console.error("Error:", error);
            toastr.error("Đã xảy ra lỗi trong quá trình gửi bình luận.");
        });
});

//  Load bình luận lên trang
    async function fetchComments() {
    const urlParams = new URLSearchParams(window.location.search);
    const bookId = urlParams.get("book_id");

    try {
        const response = await fetch(`/get_comments/${bookId}`);
        if (!response.ok) {
            throw new Error("Lỗi khi lấy dữ liệu bình luận từ server.");
        }
        const data = await response.json();

        // Lấy container bình luận để cập nhật dữ liệu
        const commentsContainer = document.querySelector("#comments-container");
        commentsContainer.innerHTML = '';  // Xóa nội dung cũ để cập nhật dữ liệu mới

        // Duyệt qua dữ liệu để tạo các phần tử bình luận mới
        data.forEach(comment => {
            const newComment = document.createElement("div");
            newComment.classList.add("sin-rattings", "mb-4");
            newComment.innerHTML = `
                <div class="star-author-all mb-2 clearfix">
                    <div class="ratting-author float-start">
                        <h5 class="float-start me-3">${comment.user_name}</h5>
                        <span>${comment.created_at}</span>
                    </div>
                    <div class="ratting-star float-end">
                        <span class="rating-stars me-2">
                            ${Array.from({ length: 5 }, (_, i) => i + 1).map(i => `
                                <i class="bi bi-star-fill${i <= comment.rating ? ' active' : ''}"></i>
                            `).join('')}
                        </span>
                        <span>(${comment.rating})</span>
                    </div>
                </div>
                <p>${comment.comment}</p>
            `;
            commentsContainer.appendChild(newComment);
        });
    } catch (error) {
        console.error("Error fetching comments:", error);
        toastr.error("Có lỗi khi tải bình luận.");
    }
}
//Thêm sách vào DS yêu thích
document.getElementById('favourite-form').addEventListener('submit', function(e) {
    e.preventDefault();
    fetch(window.location.href, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            toastr.success(data.message); // Thông báo thành công
        } else if (data.error) {
            toastr.error(data.error); // Hiển thị lỗi
        }
    })
    .catch(error => console.error('Error:', error));
});