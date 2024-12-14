const searchInput = document.getElementById('searchInput');
        const toggleSearch = document.getElementById('toggleSearch');
        const resultsContainer = document.getElementById('searchResults');

        toggleSearch.addEventListener('click', () => {
            if (searchInput.style.display === 'none' || searchInput.style.display === '') {
                searchInput.style.display = 'block';
                searchInput.focus();
                resultsContainer.style.display = 'block';
            } else {
                searchInput.style.display = 'none';
                resultsContainer.style.display = 'none';
            }
        });

        searchInput.addEventListener('input', function () {
            const query = this.value.trim();
            resultsContainer.innerHTML = ''; // Clear old results

            if (query.length === 0) return;

            fetch(`/search?q=${encodeURIComponent(query)}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.data.length === 0) {
                        resultsContainer.innerHTML = '<li class="list-group-item">Không tìm thấy kết quả</li>';
                        return;
                    }

                    data.data.forEach(book => {

                        const formattedPrice = new Intl.NumberFormat('vi-VN', {
                            style: 'currency',
                            currency: 'VND',
                            minimumFractionDigits: 0,
                        }).format(book.price);

                        const li = document.createElement('li');
                        li.className = 'list-group-item d-flex align-items-center';
                        li.innerHTML = `<img src="${book.image}" alt="${book.name}" style="width: 50px; height: 50px; object-fit: scale-down; margin-right: 10px;">
                                        <div>
                                            <strong>${book.name}</strong><br>
                                            <small>Giá: ${formattedPrice}</small>
                                        </div>
                                        `;
                        li.addEventListener('click', () => {
                            window.location.href = `/details?book_id=${book.id}`;
                        });
                        resultsContainer.appendChild(li);
                    });
                })
                .catch(err => {
                    console.error('Lỗi khi tìm kiếm:', err);
                    resultsContainer.innerHTML = '<li class="list-group-item text-danger">Lỗi khi tải dữ liệu</li>';
                });
        });

        searchInput.addEventListener('keydown', function (event) {
            if (event.key === 'Enter') {
                const query = this.value.trim();
                if (query.length > 0) {
                    window.location.href = `/search_result?q=${encodeURIComponent(query)}`;
                }
            };

        })



