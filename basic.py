from src.files import output_to_excel
from src.generate_instances import get_instances_up_to


if __name__ == "__main__":
    """
    Save cashflow output to excel for upcoming months
    """
    all_instances = get_instances_up_to()

    print("Spare Capital", "${:,.2f}".format(all_instances[0]["WIGGLE"]))

    output_to_excel(all_instances)
