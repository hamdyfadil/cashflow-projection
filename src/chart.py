
def chart_expense_shares(final_aggregate_states):
    pass
    # # Make expenses shares
    # sizes, labels = [], []
    # for pool, agg_state in filter(
    #     lambda x: x[0] != "ALL" and x[1]["EXPENSES"] < 0,
    #     final_aggregate_states.items()
    # ):
    #     sizes.append(abs(agg_state["EXPENSES"]))
    #     labels.append(pool)
    # fig1, ax1 = plt.subplots()
    # ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    # ax1.axis('equal')
    # plt.savefig("expenses.png")

    # # Make allocation graph
    # income = sum(map(
    #     lambda agg_state: agg_state[1]["INCOME"],
    #     filter(
    #         lambda x: x[0] != "ALL" and x[1]["INCOME"] > 0,
    #         final_aggregate_states.items()
    #     )
    # ))
    # sizes.append(income - sum(sizes))
    # labels.append("Unspent Income")
    # fig1, ax1 = plt.subplots()
    # ax1.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    # ax1.axis('equal')
    # plt.savefig("allocation.png")


def graph_aggregates(instances):
    pass
    # for metric in AGGREGATORS.keys():
    #     plt.plot(map(lambda x: x[metric], instances))
    #     plt.title(metric)
    #     plt.savefig("{}.png".format(metric))
    #     plt.clf()
