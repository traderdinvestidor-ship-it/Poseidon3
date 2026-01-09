def get_allocation_strategy(profile_type):
    """
    Returns a dictionary of asset allocation % based on the profile type.
    Profile Types: 'Conservador', 'Moderado', 'Arrojado'
    """
    
    strategies = {
        'Conservador': {
            'Renda Fixa': 0.80,
            'FIIs': 0.10,
            'Ações BR': 0.05,
            'Exterior': 0.05,
            'Cripto': 0.00
        },
        'Moderado': {
            'Renda Fixa': 0.40,
            'FIIs': 0.25,
            'Ações BR': 0.20,
            'Exterior': 0.10,
            'Cripto': 0.05
        },
        'Arrojado': {
            'Renda Fixa': 0.20,
            'FIIs': 0.20,
            'Ações BR': 0.30,
            'Exterior': 0.20,
            'Cripto': 0.10
        }
    }
    
    return strategies.get(profile_type, strategies['Moderado'])

def recommend_sectors(profile_type):
    if profile_type == 'Conservador':
        return ["Bancos", "Elétricas", "Seguros"]
    elif profile_type == 'Moderado':
        return ["Bancos", "Elétricas", "Varejo", "Industria"]
    else:
        return ["Tecnologia", "Varejo", "Small Caps", "Commodities"]
