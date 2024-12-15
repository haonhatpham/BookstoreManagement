from app import dao
def cart_stats(cart):
    total_amount, total_quantity = 0, 0

    if cart:
        for c in cart.values():
            total_quantity += c['quantity']
            total_amount += c['quantity'] * c['unit_price']

    return {
        'total_amount': total_amount,
        'total_quantity': total_quantity
    }


def statistic_revenue():
    results = dao.statistic_revenue()
    # for data in results:
    #     print(data)
    return [data[1] for data in dao.statistic_revenue()]


def statistic_book_by_month(month):
    sql_result = dao.stat_book_by_month(month)
    if sql_result is None:
        return None
    total_quantity = 0
    for res in sql_result:
        total_quantity += res[2]
    data = []
    index = 1
    for res in sql_result:
        temp = {}
        temp['index'] = index
        temp['name'] = res[0]
        temp['category'] = res[1]
        temp['quantity'] = res[2]
        temp['percentage'] = round((res[2] / total_quantity) * 100, 2)
        data.append(temp)
        index += 1
    return data


def statistic_category_by_month(month):
    sql_result = dao.stat_category_by_month(month)
    if sql_result is None:
        return None

    total_revenue = 0
    for res in sql_result:
        total_revenue += res[2]
    data = []
    index = 1
    for res in sql_result:
        temp = {}
        temp['index'] = index
        temp['name'] = res[0]
        temp['revenue'] = res[2]
        temp['number_of_purchases'] = res[1]
        temp['percentage'] = round((res[2] / total_revenue) * 100, 2)
        data.append(temp)
        index += 1
    return data