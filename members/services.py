def members_statement(member):
    """
    Generate a statement for a member, including their levies and payments.
    """
    levies = member.levies.all().order_by("period")
    payments = member.payments.all().order_by("payment_date")

    statement = {
        "member": member,
        "levies": [],
        "payments": [],
        "total_levy_due": member.total_levy_due,
        "total_levy_paid": member.total_levy_paid,
        "outstanding_balance": member.outstanding_balance,
    }

    for levy in levies:
        statement["levies"].append({
            "period": levy.period,
            "amount_due": levy.amount_due,
            "amount_paid": levy.amount_paid,
            "outstanding_balance": levy.balance,
            "status": levy.status,
        })

    for payment in payments:
        statement["payments"].append({
            "amount": payment.amount,
            "payment_method": payment.payment_method,
            "reference": payment.reference,
            "payment_date": payment.payment_date,
        })

    return statement
