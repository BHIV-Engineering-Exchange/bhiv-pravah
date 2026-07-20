const express = require('express');
const router = express.Router();
const aiReviewService = require('../services/aiReviewService');
const TaskSubmission = require('../models/TaskSubmission');
const auth = require('../middleware/auth');
const adminAuth = require('../middleware/adminAuth');

// Review single submission
router.post('/review-submission', auth, adminAuth, async (req, res) => {
  try {
    const { taskId, submissionId, repositoryUrl, aiProvider = 'openai' } = req.body;

    if (!taskId || !submissionId || !repositoryUrl) {
      return res.status(400).json({
        error: 'Missing required fields',
        message: 'taskId, submissionId, and repositoryUrl are required'
      });
    }

    const review = await aiReviewService.reviewSubmission(
      taskId,
      submissionId,
      repositoryUrl,
      req.user.id,
      aiProvider
    );

    res.json({
      success: true,
      message: 'AI review completed successfully',
      review: {
        id: review._id,
        overallScore: review.overallScore,
        completionPercentage: review.completionPercentage,
        summary: review.aiSummary,
        status: review.reviewStatus
      }
    });
  } catch (error) {
    console.error('Error reviewing submission:', error);
    res.status(500).json({
      error: 'Failed to review submission',
      message: error.message
    });
  }
});

// Bulk review submissions
router.post('/bulk-review', auth, adminAuth, async (req, res) => {
  try {
    const { submissionIds, aiProvider = 'openai' } = req.body;

    if (!submissionIds || !Array.isArray(submissionIds)) {
      return res.status(400).json({
        error: 'Invalid input',
        message: 'submissionIds must be an array'
      });
    }

    const results = await aiReviewService.bulkReviewSubmissions(
      submissionIds,
      req.user.id,
      aiProvider
    );

    const successCount = results.filter(r => r.success).length;
    const failureCount = results.filter(r => !r.success).length;

    res.json({
      success: true,
      message: `Bulk review completed: ${successCount} successful, ${failureCount} failed`,
      results,
      summary: {
        total: submissionIds.length,
        successful: successCount,
        failed: failureCount
      }
    });
  } catch (error) {
    console.error('Error in bulk review:', error);
    res.status(500).json({
      error: 'Failed to perform bulk review',
      message: error.message
    });
  }
});

// Get review details
router.get('/review/:reviewId', auth, async (req, res) => {
  try {
    const { reviewId } = req.params;
    const review = await aiReviewService.getReviewById(reviewId);

    if (!review) {
      return res.status(404).json({
        error: 'Review not found',
        message: 'The specified review does not exist'
      });
    }

    res.json({
      success: true,
      review
    });
  } catch (error) {
    console.error('Error getting review:', error);
    res.status(500).json({
      error: 'Failed to get review',
      message: error.message
    });
  }
});

// Get reviews for a task
router.get('/task/:taskId/reviews', auth, async (req, res) => {
  try {
    const { taskId } = req.params;
    const reviews = await aiReviewService.getReviewsByTask(taskId);

    res.json({
      success: true,
      reviews,
      count: reviews.length
    });
  } catch (error) {
    console.error('Error getting task reviews:', error);
    res.status(500).json({
      error: 'Failed to get task reviews',
      message: error.message
    });
  }
});

// Get pending submissions for review
router.get('/pending-submissions', auth, adminAuth, async (req, res) => {
  try {
    const { limit = 20 } = req.query;

    // Find submissions that haven't been AI reviewed yet
    const submissions = await TaskSubmission.find({
      repositoryUrl: { $exists: true, $ne: null }
    })
    .populate('task', 'title description priority dueDate')
    .populate('user', 'name email')
    .sort({ submittedAt: -1 })
    .limit(parseInt(limit));

    // Filter out already reviewed submissions
    const pendingSubmissions = [];
    for (const submission of submissions) {
      const existingReview = await aiReviewService.getReviewsByTask(submission.task._id);
      const hasReview = existingReview.some(review => 
        review.submissionId.toString() === submission._id.toString()
      );
      
      if (!hasReview) {
        pendingSubmissions.push({
          _id: submission._id,
          task: submission.task,
          user: submission.user,
          repositoryUrl: submission.repositoryUrl,
          submittedAt: submission.submittedAt,
          notes: submission.notes
        });
      }
    }

    res.json({
      success: true,
      pendingSubmissions,
      count: pendingSubmissions.length
    });
  } catch (error) {
    console.error('Error getting pending submissions:', error);
    res.status(500).json({
      error: 'Failed to get pending submissions',
      message: error.message
    });
  }
});

// Auto-review all pending submissions
router.post('/auto-review-pending', auth, adminAuth, async (req, res) => {
  try {
    const { aiProvider = 'openai', limit = 10 } = req.body;

    // Get pending submissions
    const submissions = await TaskSubmission.find({
      repositoryUrl: { $exists: true, $ne: null }
    })
    .populate('task')
    .sort({ submittedAt: -1 })
    .limit(parseInt(limit));

    const submissionIds = [];
    for (const submission of submissions) {
      const existingReviews = await aiReviewService.getReviewsByTask(submission.task._id);
      const hasReview = existingReviews.some(review => 
        review.submissionId.toString() === submission._id.toString()
      );
      
      if (!hasReview) {
        submissionIds.push(submission._id);
      }
    }

    if (submissionIds.length === 0) {
      return res.json({
        success: true,
        message: 'No pending submissions found for review',
        results: []
      });
    }

    const results = await aiReviewService.bulkReviewSubmissions(
      submissionIds,
      req.user.id,
      aiProvider
    );

    const successCount = results.filter(r => r.success).length;

    res.json({
      success: true,
      message: `Auto-reviewed ${successCount} submissions`,
      results,
      summary: {
        total: submissionIds.length,
        successful: successCount,
        failed: results.length - successCount
      }
    });
  } catch (error) {
    console.error('Error in auto-review:', error);
    res.status(500).json({
      error: 'Failed to auto-review submissions',
      message: error.message
    });
  }
});

// Get review statistics
router.get('/statistics', auth, adminAuth, async (req, res) => {
  try {
    const { days = 30 } = req.query;
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - parseInt(days));

    const stats = await AIReview.aggregate([
      {
        $match: {
          reviewedAt: { $gte: startDate }
        }
      },
      {
        $group: {
          _id: null,
          totalReviews: { $sum: 1 },
          avgOverallScore: { $avg: '$overallScore' },
          avgCompletionPercentage: { $avg: '$completionPercentage' },
          avgCodeQualityScore: { $avg: '$codeQualityScore' },
          completedReviews: {
            $sum: {
              $cond: [{ $eq: ['$reviewStatus', 'completed'] }, 1, 0]
            }
          },
          failedReviews: {
            $sum: {
              $cond: [{ $eq: ['$reviewStatus', 'failed'] }, 1, 0]
            }
          }
        }
      }
    ]);

    const statistics = stats[0] || {
      totalReviews: 0,
      avgOverallScore: 0,
      avgCompletionPercentage: 0,
      avgCodeQualityScore: 0,
      completedReviews: 0,
      failedReviews: 0
    };

    res.json({
      success: true,
      statistics: {
        ...statistics,
        successRate: statistics.totalReviews > 0 
          ? Math.round((statistics.completedReviews / statistics.totalReviews) * 100)
          : 0,
        avgOverallScore: Math.round(statistics.avgOverallScore || 0),
        avgCompletionPercentage: Math.round(statistics.avgCompletionPercentage || 0),
        avgCodeQualityScore: Math.round(statistics.avgCodeQualityScore || 0)
      },
      period: `Last ${days} days`
    });
  } catch (error) {
    console.error('Error getting statistics:', error);
    res.status(500).json({
      error: 'Failed to get statistics',
      message: error.message
    });
  }
});

module.exports = router;