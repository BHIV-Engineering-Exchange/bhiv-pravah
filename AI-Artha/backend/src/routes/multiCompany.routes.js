import express from 'express';
import multiCompanyController from '../controllers/multiCompany.controller.js';
import { protect, authorize } from '../middleware/auth.js';

const router = express.Router();

router.use(protect);

router.post('/companies', multiCompanyController.createCompany);
router.get('/companies', multiCompanyController.getCompanies);
router.get('/companies/:id', multiCompanyController.getCompany);
router.put('/companies/:id', multiCompanyController.updateCompany);

router.post('/companies/:companyId/branches', multiCompanyController.createBranch);
router.get('/companies/:companyId/branches', multiCompanyController.getBranches);

router.post('/companies/:companyId/consolidated-report', multiCompanyController.getConsolidatedReport);
router.post('/consolidated-trial-balance', multiCompanyController.getConsolidatedTrialBalance);

router.post('/cost-centres', multiCompanyController.createCostCentre);
router.get('/cost-centres', multiCompanyController.getCostCentres);

export default router;
