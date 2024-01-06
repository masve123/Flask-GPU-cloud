"""
This is where we set up our API endpoints for GPU usage.
"""

from flask import request, jsonify
from app.models import GPU_booking, GPU_usage, User, GPU_instance, GPU_status, GPU_queue_entry, GPU_queue_status
from flask import current_app as app
from app import db

from flask import Blueprint

from datetime import datetime, timedelta
from sqlalchemy import func

gpu_usage_blueprint = Blueprint('gpu_usage', __name__)

############## GPU Usage endpoint functions ##############
# Endpoint to update the usage details
@gpu_usage_blueprint.route('/update/<int:usage_id>', methods=['PUT'])
def update_gpu_usage(usage_id):
    """
    Update GPU usage details
    ---
    tags:
      - GPU Usage
    description: Update the usage details of a specific GPU instance.
    parameters:
      - name: usage_id
        in: path
        type: integer
        required: true
        description: ID of the GPU usage record to be updated.
      - in: body
        name: body
        schema:
          id: GPUUsageUpdate
          properties:
            usage_duration:
              type: integer
              description: The new usage duration in minutes.
    responses:
      200:
        description: GPU usage updated successfully.
      404:
        description: GPU usage record not found.
    """
    usage = GPU_usage.query.get(usage_id)
    if not usage:
        return jsonify({'message': 'GPU usage record not found'}), 404

    data = request.json
    usage.usage_duration = data.get('usage_duration', usage.usage_duration)
    db.session.commit()
    return jsonify({'message': 'GPU usage updated successfully!'}), 200


# An endpoint to start tracking the usage of a GPU instance.
@gpu_usage_blueprint.route('/start', methods=['POST'])
def start_gpu_usage():
    """
    Start tracking GPU usage
    ---
    tags:
      - GPU Usage
    description: Start tracking the actual usage of a GPU instance.
    parameters:
      - in: body
        name: body
        schema:
          id: GPUUsageStart
          required:
            - gpu_id
            - booking_id
          properties:
            gpu_id:
              type: integer
              description: ID of the GPU instance being used.
            booking_id:
              type: integer
              description: ID of the booking related to the usage.
    responses:
      201:
        description: GPU usage tracking started.
      404:
        description: GPU instance or booking not found.
      400:
        description: Booking does not match GPU instance or tracking already started.
    """
    try:
        data = request.json

        # Check if GPU instance exists
        gpu_instance = GPU_instance.query.get(data['gpu_id'])
        if not gpu_instance:
            return jsonify({'message': 'GPU instance not found'}), 404

        # Check if booking exists and matches the GPU instance
        booking = GPU_booking.query.get(data['booking_id'])
        if not booking or booking.gpu_id != gpu_instance.id:
            return jsonify({'message': 'Booking not found or does not match GPU instance'}), 404

        # Check if usage tracking is already started
        existing_usage = GPU_usage.query.filter_by(gpu_id=gpu_instance.id, booking_id=booking.booking_id, end_time=None).first()
        if existing_usage:
            return jsonify({
                'message': 'GPU usage tracking already started for this booking',
                'usage_id': existing_usage.usage_id
            }), 400

        # Start tracking GPU usage
        usage = GPU_usage(gpu_id=gpu_instance.id, booking_id=booking.booking_id, usage_duration=0) # Initialize with zero
        gpu_instance.status = GPU_status.IN_USE
        db.session.add(usage)
        db.session.commit()

        return jsonify({
            'message': 'GPU usage tracking started!',
            'usage_id': usage.usage_id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500







# An endpoint to stop tracking the usage of a GPU instance.
@gpu_usage_blueprint.route('/stop/<int:usage_id>', methods=['POST'])
def stop_gpu_usage(usage_id):
    """
    Stop tracking GPU usage
    ---
    tags:
      - GPU Usage
    description: Stop tracking the usage of a GPU instance.
    parameters:
      - name: usage_id
        in: path
        type: integer
        required: true
        description: ID of the GPU usage record to stop tracking.
    responses:
      200:
        description: GPU usage tracking stopped.
      404:
        description: GPU usage record not found.
    """
    usage = GPU_usage.query.get(usage_id)
    if not usage:
        return jsonify({'message': 'GPU usage record not found'}), 404

    # Update the usage record
    usage.end_time = datetime.utcnow()
    db.session.commit()

    # Update the GPU instance status
    gpu_instance = GPU_instance.query.get(usage.gpu_id)
    if gpu_instance:
        gpu_instance.status = GPU_status.AVAILABLE
        db.session.commit()

    return jsonify({'message': 'GPU usage tracking stopped!'}), 200

# An endpoint to get all active GPU usage records.
@gpu_usage_blueprint.route('/active', methods=['GET'])
def get_active_gpus():
    """
    Get all active GPU usage records
    ---
    tags:
      - GPU Usage
    description: Retrieve a list of all active GPU usage records.
    responses:
      200:
        description: A list of active GPU usage records.
    """
    active_usages = GPU_usage.query.filter(GPU_usage.end_time.is_(None)).all()
    return jsonify([usage.to_dict() for usage in active_usages])


# An endpoint to generate a report for a specific GPU's usage over the past 24 hours.
@gpu_usage_blueprint.route('/report/<int:gpu_id>', methods=['GET'])
def gpu_usage_report(gpu_id):
    """
    Generate a GPU usage report
    ---
    tags:
      - GPU Usage
    description: Generate a report for a specific GPU's usage over the past 24 hours.
    parameters:
      - name: gpu_id
        in: path
        type: integer
        required: true
        description: ID of the GPU to generate the report for.
    responses:
      200:
        description: A report of the GPU's usage over the past 24 hours.
    """
    last_24_hours = datetime.utcnow() - timedelta(days=1)
    usage_records = GPU_usage.query.filter(
        GPU_usage.gpu_id == gpu_id,
        GPU_usage.start_time >= last_24_hours
    ).all()

    # Fetch the GPU instance
    gpu_instance = GPU_instance.query.get(gpu_id)
    if not gpu_instance:
        return jsonify({'message': 'GPU instance not found'}), 404

    # Aggregating metrics from GPU_usage
    total_usage_duration = sum([record.usage_duration for record in usage_records if record.usage_duration])

    # Extracting metrics from GPU_instance
    utilization_percentage = gpu_instance.utilization_percentage
    peak_memory_usage = gpu_instance.peak_memory_usage
    average_load = gpu_instance.average_load

    # Creating the report
    report = {
        'gpu_id': gpu_id,
        'total_usage_duration_last_24_hours': total_usage_duration,
        'utilization_percentage': utilization_percentage,
        'peak_memory_usage_MB': peak_memory_usage,
        'average_load_percentage': average_load
    }

    return jsonify(report)
