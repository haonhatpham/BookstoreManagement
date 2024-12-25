if (window.location.pathname === '/details') {
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
                rating: rating
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

                    document.querySelector("#comment").value='';
                    document.querySelector("#rating").value='';
                }
            })
            .catch((error) => {
                console.error("Error:", error);
                toastr.error("Đã xảy ra lỗi trong quá trình gửi bình luận.");
            });
    });

    // xóa bình luận
    document.addEventListener('DOMContentLoaded', () => {
        document.querySelector("#comments-container").addEventListener("click", async (event) => {

            const reviewId = event.target.getAttribute('data-id');
            const bookId = event.target.getAttribute('data-book-id');

            if (event.target.classList.contains('btn-delete')) {
                event.preventDefault(); // Ngăn hành vi mặc định của nút

                // Hiển thị hộp thoại xác nhận với Toastr
                toastr.warning('<p>Bạn có chắc chắn muốn xóa bình luận này?</p><button type="button" id="confirm-delete" class="btn btn-danger btn-sm">Xóa</button>', 'Xác nhận xóa', {
                    closeButton: true,
                    allowHtml: true,
                    onShown: function () {
                        document.getElementById('confirm-delete').onclick = async function () {
                            try {
                                // Gửi yêu cầu xóa bình luận
                                const response = await fetch(`/delete_review?review_id=${reviewId}&book_id=${bookId}`, {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json',
                                    },
                                });

                                if (!response.ok) {
                                    throw new Error('Lỗi khi xóa bình luận.');
                                }

                                const data = await response.json();
                                if (data.success) {
                                    toastr.success(data.message);
                                    // Tải lại danh sách bình luận
                                    fetchComments();
                                } else {
                                    toastr.error(data.error);
                                }
                            } catch (error) {
                                console.error("Error:", error);
                                toastr.error('Đã xảy ra lỗi khi xóa bình luận.');
                            }
                        };
                    }
                });
            }else if (event.target.classList.contains('btn-warning')) { // chỉnh sửa bình luận
                event.preventDefault();

                // Tìm phần tử chứa bình luận để thêm form chỉnh sửa
                const commentElement = event.target.closest('.sin-rattings');

                // Lấy giá trị rating hiện tại từ phần tử bình luận

                const currentRating = commentElement.getAttribute('data-rating');

                // Tạo form chỉnh sửa
                const editFormHtml = `
                    <div class="edit-form mt-3">
                        <label for="edit-comment">Nội dung bình luận:</label>
                        <textarea id="edit-comment" class="form-control" rows="3">${commentElement.querySelector('#comment-text').innerText}</textarea>
                        <div class="mt-2">
                            <label for="edit-rating">Cho sao:</label>
                            <select id="edit-rating" class="form-select">
                                ${Array.from({ length: 5 }, (_, i) =>
                                    `<option value="${i + 1}" ${i + 1 == commentElement.getAttribute('data-rating') ? 'selected' : ''}>${i + 1}</option>`
                                ).join('')}
                            </select>
                        </div>
                        <button type="button" id="submit-edit" class="btn btn-success mt-2">Lưu chỉnh sửa</button>
                        <button type="button" id="cancel-edit" class="btn btn-secondary mt-2 ms-2">Hủy</button>
                    </div>
                `;
                if (document.querySelector('.edit-form')) {
                    return;
                }
                // Chèn form chỉnh sửa vào dưới bình luận
                commentElement.insertAdjacentHTML('afterend', editFormHtml);

                // Thêm logic xử lý sự kiện cho nút "Lưu chỉnh sửa"
                document.getElementById('submit-edit').onclick = async function () {

                    const comment = document.getElementById('edit-comment').value;
                    const rating = document.getElementById('edit-rating').value;
                    if (!comment || !rating) {
                        toastr.error('Vui lòng điền đầy đủ nội dung và xếp hạng.');
                        return;
                    }

                    try {
                        const response = await fetch('/edit_review', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                review_id: reviewId,
                                comment: comment,
                                rating: rating,
                                book_id: bookId
                            }),
                        });
                            console.log(response)
                        if (!response.ok) {
                            throw new Error('Lỗi khi chỉnh sửa bình luận.');
                        }

                        const data = await response.json();
                        if (data.message) {
                            toastr.success('Chỉnh sửa thành công!');
                            fetchComments();
                            document.querySelector('.edit-form').remove();
                        } else if (data.error) {
                            toastr.error(data.error);
                        }
                    } catch (error) {
                        console.error("Error:", error);
                        toastr.error('Đã xảy ra lỗi khi chỉnh sửa bình luận.');
                    }
                };

                // Thêm logic xử lý sự kiện cho nút "Hủy"
                document.getElementById('cancel-edit').onclick = function () {
                    document.querySelector('.edit-form').remove();
                };
            }

        });
    });

    // Hàm tải danh sách bình luận
    async function fetchComments() {
        const urlParams = new URLSearchParams(window.location.search);
        const bookId = urlParams.get("book_id");

        try {
            const response = await fetch(`/get_comments/${bookId}`);
            if (!response.ok) {
                throw new Error("Lỗi khi lấy dữ liệu bình luận từ server.");
            }
            const data = await response.json();

            const commentsContainer = document.querySelector("#comments-container");
            commentsContainer.innerHTML = '';  // Xóa nội dung cũ để cập nhật dữ liệu mới

            const current_user_id = data['current_user_id'];
            const current_user_role = data['current_user_role'];

            data['comments'].forEach(comment => {
                const newComment = document.createElement("div");
                newComment.classList.add("sin-rattings", "mb-4");
                newComment.setAttribute('data-rating', comment.rating);
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
                    <p id='comment-text'>${comment.comment}</p>
                `;
                if (comment.user_id == current_user_id || current_user_role == 1) {
                    newComment.innerHTML += `
                        <div class="d-flex justify-content-end">
                            <button data-id="${comment.id}" data-book-id="${bookId}" class="btn btn-warning btn-sm me-2 btn-edit">Sửa</button>
                            <button class="btn btn-danger btn-sm btn-delete" data-id="${comment.id}" data-book-id="${bookId}">Xóa</button>
                        </div>
                    `;
                }
                commentsContainer.appendChild(newComment);
            });
        } catch (error) {
            console.error("Error fetching comments:", error);
            toastr.error("Có lỗi khi tải bình luận.");
        }
    }
}


document.addEventListener("DOMContentLoaded", function () {
    const toggleBtn = document.querySelector(".toggle-btn");
    const textContainer = document.querySelector(".text-container");

    toggleBtn.addEventListener("click", function () {
        textContainer.classList.toggle("expanded");
        if (textContainer.classList.contains("expanded")) {
            toggleBtn.textContent = "Thu gọn";
            toggleBtn.style.transform = "translate(-50%, 0)"; // Đặt lại vị trí sau khi mở
        } else {
            toggleBtn.textContent = "Hiển thị thêm";
            toggleBtn.style.transform = "translate(-50%, 0)"; // Quay lại vị trí ban đầu
        }
    });
});

