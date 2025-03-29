import pandas as pd
import xml.etree.ElementTree as ET

# Load the export.xml file
tree = ET.parse('export.xml')
root = tree.getroot()

# Relevant types for stress, fitness, and mental health
relevant_types = [
    # Stress & Mental Health
    'HKQuantityTypeIdentifierHeartRateVariabilitySDNN',
    'HKQuantityTypeIdentifierRestingHeartRate',
    'HKCategoryTypeIdentifierSleepAnalysis',
    'HKCategoryTypeIdentifierAudioExposureEvent',
    
    # Fitness & Exercise
    'HKQuantityTypeIdentifierActiveEnergyBurned',
    'HKQuantityTypeIdentifierDistanceWalkingRunning',
    'HKQuantityTypeIdentifierAppleExerciseTime',
    'HKQuantityTypeIdentifierStepCount',
    'HKQuantityTypeIdentifierVO2Max',
    'HKQuantityTypeIdentifierWalkingHeartRateAverage',
]

records = []

# Extract relevant data
for record in root.findall('Record'):
    rec_type = record.get('type')
    if rec_type in relevant_types:
        records.append({
            'type': rec_type,
            'value': record.get('value'),
            'unit': record.get('unit'),
            'startDate': record.get('startDate'),
            'endDate': record.get('endDate'),
            'source': record.get('sourceName')
        })

df = pd.DataFrame(records)

# Save to CSV for further exploration
df.to_csv('mental_health_fitness_data.csv', index=False)

print(df['type'].value_counts())
print(df.head())
