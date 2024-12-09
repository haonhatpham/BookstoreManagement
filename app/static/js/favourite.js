
// xóa sp yêu thích
    function deleteFavourite(bookId) {
    fetch('/delete_favourite', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `book_id=${bookId}`
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('Server response:', data);
        if (data.message) {
            toastr.success(data.message);
            reloadFavourites();
        } else {
            toastr.error(data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// hàm bổ trợ cho xóa sp yêu thích
function reloadFavourites() {
    fetch('/get_favourites_json', {
        method: 'GET'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error();
        }
        return response.json();
    })
    .then(data => {
        const container = document.querySelector('#favourites-container');
        container.innerHTML = ''; // Xóa nội dung cũ

        if (data.favourite_books && data.favourite_books.length > 0) {
            data.favourite_books.forEach(book => {
                const bookElement = document.createElement('div');
                bookElement.classList.add('col-lg-6');
                bookElement.id = `book-${book.id}`;
                bookElement.innerHTML = `
                    <figure class="d-flex align-items-center m-0">
                        <div class="aside"><img src="${book.image}" width="80" height="80"></div>
                        <figcaption class="ps-3">
                            <a href="/details?book_id=${book.id}">${book.name}</a>
                            <p class="mb-2">
                                <span class="price">${book.price.toLocaleString()}₫</span>
                                <span class="ms-2 text-muted text-decoration-line-through">
                                    ${book.unit_price.toLocaleString()}₫
                                </span>
                            </p>
                            <span>
                                <input style="display: none;" type="number" id="quantity" class="form-control w-50" value="1" min="1" max="1000" step="1"/>
                                <a href="javascript:;" onclick="addToCart(${book.id}, '${book.image}', '${book.name}', ${book.unit_price})" class="btn btn-light ms-2">Thêm vào giỏ hàng</a>
                            </span>
                            <button type="button" class="btn btn-danger btn-sm ms-1" title="Xóa khỏi danh sách yêu thích"
                                onclick="deleteFavourite(${book.id})">
                                <i class="bi bi-trash"></i>
                            </button>
                        </figcaption>
                    </figure>
                `;
                container.appendChild(bookElement);
            });
        } else {
            container.innerHTML = '<h2 class="text-center">Không có sản phẩm yêu thích!</h2>';
        }
    })
    .catch(error => {
        console.error("Error fetching data:", error);
        toastr.error("Có lỗi khi tải danh sách yêu thích.");
    });
}